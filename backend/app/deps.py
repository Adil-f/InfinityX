from __future__ import annotations

import hmac
import uuid

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ApiKey, User
from app.security import API_SCOPE_PERMISSIONS, Principal, decode_token, hash_api_key, utcnow


def get_principal(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Principal:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc
        if payload.get("typ") != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
        try:
            user_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc
        user = db.query(User).filter(User.id == user_id).one_or_none()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="Invalid token")
        if user.must_change_password:
            raise HTTPException(status_code=403, detail="Change the temporary password before using the API")
        return Principal(
            user_id=user.id,
            org_id=user.org_id,
            role=user.role,
            auth="jwt",
            email=user.email,
            full_name=user.full_name,
            is_fixture=user.is_fixture,
            actor_id=user.id,
        )
    if x_api_key:
        digest = hash_api_key(x_api_key)
        key = db.query(ApiKey).filter(ApiKey.key_hash == digest).one_or_none()
        if not key or key.revoked_at is not None or not hmac.compare_digest(key.key_hash, digest):
            raise HTTPException(status_code=401, detail="Invalid API key")
        scopes: set[str] = set()
        for scope in key.scopes.split(","):
            scopes |= API_SCOPE_PERMISSIONS.get(scope.strip(), set())
        creator = db.query(User).filter(User.id == key.created_by).one_or_none() if key.created_by else None
        if not creator or creator.status != "active" or creator.org_id != key.org_id:
            raise HTTPException(status_code=401, detail="Invalid API key")
        key.last_used_at = utcnow()
        db.commit()
        return Principal(
            user_id=None,
            org_id=key.org_id,
            role=creator.role,
            auth="api_key",
            email=None,
            full_name=None,
            scopes=scopes,
            api_key_id=key.id,
            actor_id=creator.id,
        )
    raise HTTPException(status_code=401, detail="Authentication required")


def require(permission: str):
    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.allows(permission):
            raise HTTPException(status_code=403, detail="Missing permission")
        return principal

    return dependency


def require_session(principal: Principal) -> None:
    if principal.auth == "api_key" or principal.user_id is None:
        raise HTTPException(status_code=403, detail="API keys cannot use this user-session route")
