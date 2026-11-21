from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_principal, require_session
from app.models import AuditLog, ConsentRecord, CreditLedger, Organization, User
from app.security import (
    PLANS,
    Principal,
    hash_password,
    make_token,
    permissions_for,
    slugify,
    utcnow,
    validate_password,
    verify_password,
    decrypt_secret,
    encrypt_secret,
    new_totp_secret,
    totp_uri,
    verify_totp,
    decode_token,
)
from app.services.ratelimit import allow, limit_for

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: str
    password: str
    full_name: str = Field(min_length=2, max_length=120)
    organization: str = Field(min_length=2, max_length=120)
    accept_terms: bool


class LoginIn(BaseModel):
    email: str
    password: str


class MfaCode(BaseModel):
    code: str


class MfaSetupIn(BaseModel):
    current_code: str | None = None


class MfaLogin(BaseModel):
    mfa_token: str
    code: str


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def _public_user(user: User, org: Organization) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "org_id": str(org.id),
        "org_name": org.name,
        "plan": org.plan,
        "credits_balance": org.credits_balance,
        "mfa_enabled": user.mfa_enabled,
        "is_fixture": user.is_fixture,
        "organization_is_fixture": org.is_fixture,
        "permissions": sorted(permissions_for(user.role)),
    }


def _note_failure(user: User) -> None:
    from datetime import timedelta

    user.failed_logins += 1
    if user.failed_logins >= 5:
        user.locked_until = utcnow() + timedelta(minutes=15)


@router.post("/register")
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request) or "unknown"
    if not allow(f"register:{ip}", limit_for("free", "login")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    if not body.accept_terms:
        raise HTTPException(status_code=422, detail="Terms must be accepted")
    problem = validate_password(body.password)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    email = body.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Email is not valid")
    if db.query(User).filter(User.email == email).one_or_none():
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    base = slugify(body.organization)
    slug = base
    suffix = 1
    while db.query(Organization).filter(Organization.slug == slug).one_or_none():
        suffix += 1
        slug = f"{base}-{suffix}"
    org = Organization(name=body.organization.strip(), slug=slug, plan="free", credits_balance=PLANS["free"]["credits"], is_fixture=False)
    db.add(org)
    db.flush()
    user = User(
        org_id=org.id,
        email=email,
        password_hash=hash_password(body.password),
        full_name=body.full_name.strip(),
        role="owner",
        is_fixture=False,
    )
    db.add(user)
    db.flush()
    db.add(CreditLedger(org_id=org.id, delta=PLANS["free"]["credits"], reason="free plan allowance"))
    db.add(ConsentRecord(org_id=org.id, user_id=user.id, purpose="Account registration", lawful_basis="contract", subject_type="account", text_version="account-v1"))
    db.add(AuditLog(org_id=org.id, user_id=user.id, action="auth.register", resource_type="user", resource_id=str(user.id), ip=_client_ip(request), details={"fixture": False}))
    db.commit()
    token = make_token(user_id=user.id, org_id=org.id, role=user.role, minutes=30, typ="access")
    return {"access_token": token, "token_type": "bearer", "user": _public_user(user, org)}


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request) or "unknown"
    email = body.email.strip().lower()
    limit = limit_for("free", "login")
    if not allow(f"login:{ip}", limit) or not allow(f"login:acct:{email}", limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    user = db.query(User).filter(User.email == email).one_or_none()
    invalid = HTTPException(status_code=401, detail="Invalid email or password")
    if not user or user.status != "active":
        raise invalid
    if user.locked_until and user.locked_until > utcnow():
        if verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")
        raise invalid
    if not verify_password(body.password, user.password_hash):
        _note_failure(user)
        db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="auth.login_failed", resource_type="user", resource_id=str(user.id), ip=ip, details={}))
        db.commit()
        raise invalid
    if user.mfa_enabled:
        token = make_token(user_id=user.id, org_id=user.org_id, role=user.role, minutes=5, typ="mfa")
        db.commit()
        return {"mfa_required": True, "mfa_token": token}
    user.failed_logins = 0
    user.locked_until = None
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="auth.login", resource_type="user", resource_id=str(user.id), ip=ip, details={}))
    db.commit()
    org = db.query(Organization).filter(Organization.id == user.org_id).one()
    token = make_token(user_id=user.id, org_id=user.org_id, role=user.role, minutes=30, typ="access")
    return {"access_token": token, "token_type": "bearer", "mfa_required": False, "user": _public_user(user, org)}


@router.post("/mfa/login")
def mfa_login(body: MfaLogin, request: Request, db: Session = Depends(get_db)):
    ip = _client_ip(request) or "unknown"
    limit = limit_for("free", "login")
    if not allow(f"mfa:{ip}", limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    try:
        payload = decode_token(body.mfa_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    if payload.get("typ") != "mfa":
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == uuid.UUID(payload["sub"])).one_or_none()
    if not user or user.status != "active" or not user.mfa_enabled or not user.mfa_secret_encrypted:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not allow(f"mfa:acct:{user.id}", limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    secret = decrypt_secret(user.mfa_secret_encrypted)
    code = body.code.strip()
    if user.locked_until and user.locked_until > utcnow():
        if secret and verify_totp(secret, code):
            raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")
        raise HTTPException(status_code=401, detail="Invalid authentication code")
    if not secret or not verify_totp(secret, code):
        _note_failure(user)
        db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="auth.login_failed", resource_type="user", resource_id=str(user.id), ip=ip, details={"mfa": True}))
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid authentication code")
    user.failed_logins = 0
    user.locked_until = None
    org = db.query(Organization).filter(Organization.id == user.org_id).one()
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="auth.login", resource_type="user", resource_id=str(user.id), ip=_client_ip(request), details={"mfa": True}))
    db.commit()
    token = make_token(user_id=user.id, org_id=user.org_id, role=user.role, minutes=30, typ="access")
    return {"access_token": token, "token_type": "bearer", "user": _public_user(user, org)}


@router.post("/mfa/setup")
def mfa_setup(body: MfaSetupIn | None = None, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    require_session(principal)
    body = body or MfaSetupIn()
    user = db.query(User).filter(User.id == principal.user_id).one()
    secret = new_totp_secret()
    encrypted = encrypt_secret(secret)
    if user.mfa_enabled:
        current = decrypt_secret(user.mfa_secret_encrypted or "")
        if not body.current_code or not current or not verify_totp(current, body.current_code.strip()):
            raise HTTPException(status_code=401, detail="Current authentication code is required to replace MFA")
        user.mfa_pending_secret_encrypted = encrypted
        db.commit()
        return {"secret": secret, "otpauth_uri": totp_uri(secret, user.email), "enabled": True, "pending": True}
    user.mfa_secret_encrypted = encrypted
    user.mfa_pending_secret_encrypted = None
    user.mfa_enabled = False
    db.commit()
    return {"secret": secret, "otpauth_uri": totp_uri(secret, user.email), "enabled": False, "pending": False}


@router.post("/mfa/verify")
def mfa_verify(body: MfaCode, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    require_session(principal)
    user = db.query(User).filter(User.id == principal.user_id).one()
    code = body.code.strip()
    if user.mfa_pending_secret_encrypted:
        pending = decrypt_secret(user.mfa_pending_secret_encrypted)
        if not pending or not verify_totp(pending, code):
            raise HTTPException(status_code=401, detail="Invalid authentication code")
        user.mfa_secret_encrypted = user.mfa_pending_secret_encrypted
        user.mfa_pending_secret_encrypted = None
        user.mfa_enabled = True
        db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="mfa.enable", resource_type="user", resource_id=str(user.id), ip=None, details={"rotated": True}))
        db.commit()
        return {"enabled": True}
    if not user.mfa_secret_encrypted:
        raise HTTPException(status_code=422, detail="MFA setup has not been started")
    secret = decrypt_secret(user.mfa_secret_encrypted)
    if not secret or not verify_totp(secret, code):
        raise HTTPException(status_code=401, detail="Invalid authentication code")
    user.mfa_enabled = True
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="mfa.enable", resource_type="user", resource_id=str(user.id), ip=None, details={}))
    db.commit()
    return {"enabled": True}


@router.get("/me")
def me(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    if principal.auth == "api_key" or not principal.user_id:
        org = db.query(Organization).filter(Organization.id == principal.org_id).one()
        return {
            "id": None,
            "email": None,
            "full_name": "API key",
            "role": "api_key",
            "org_id": str(org.id),
            "org_name": org.name,
            "plan": org.plan,
            "credits_balance": org.credits_balance,
            "mfa_enabled": False,
            "is_fixture": False,
            "organization_is_fixture": org.is_fixture,
            "permissions": sorted(principal.allows(item) and item for item in ["read", "search", "report", "investigate", "billing", "apikeys", "admin", "sources"] if principal.allows(item)),
        }
    user = db.query(User).filter(User.id == principal.user_id).one()
    org = db.query(Organization).filter(Organization.id == user.org_id).one()
    return _public_user(user, org)


@router.post("/logout")
def logout(principal: Principal = Depends(get_principal)):
    return {"status": "ok", "detail": "Discard the bearer token on the client. Server sessions are not stored."}
