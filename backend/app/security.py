from __future__ import annotations

import base64
import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pyotp
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

LAWFUL_BASES = {
    "consent",
    "legitimate_interest",
    "legal_obligation",
    "contract",
    "public_task",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "viewer": {"read"},
    "analyst": {"read", "search", "report"},
    "investigator": {"read", "search", "report", "investigate"},
    "billing": {"read", "billing", "apikeys"},
    "admin": {"read", "search", "report", "investigate", "billing", "apikeys", "admin", "sources"},
    "owner": {"read", "search", "report", "investigate", "billing", "apikeys", "admin", "sources"},
}

API_SCOPE_PERMISSIONS = {
    "search": {"search"},
    "read": {"read"},
}

PLANS = {
    "free": {"credits": 50, "searches_per_minute": 30, "list_price_eur": 0, "label": "Free"},
    "pro": {"credits": 1000, "searches_per_minute": 120, "list_price_eur": 79, "label": "Pro"},
    "enterprise": {"credits": 10000, "searches_per_minute": 600, "list_price_eur": None, "label": "Enterprise"},
}

LOCAL_MODULES = {"phone", "cnic", "forensics"}
EXTERNAL_MODULES = {"email", "username", "social", "ip", "domain", "threat", "url"}
MODULES = LOCAL_MODULES | EXTERNAL_MODULES | {"universal"}

USER_AGENT = "InfinityX-OSINT/0.1 (authorized security research)"
DISCLAIMER = (
    "This analysis separates verified observations from hypotheses. "
    "It does not accuse any person of a crime. "
    "Infrastructure indicators describe hosts, domains, or networks, not a person's conduct. "
    "Hypotheses are not findings."
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def validate_password(password: str) -> str | None:
    if len(password) < 12:
        return "Password must be at least 12 characters"
    if not re.search(r"[A-Za-z]", password):
        return "Password must include a letter"
    if not re.search(r"\d", password):
        return "Password must include a number"
    return None


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str | None:
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def make_token(*, user_id: uuid.UUID, org_id: uuid.UUID, role: str, minutes: int, typ: str) -> str:
    payload = {
        "sub": str(user_id),
        "org": str(org_id),
        "role": role,
        "typ": typ,
        "exp": utcnow() + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def new_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="Infinity X")


def verify_totp(secret: str, code: str) -> bool:
    if not re.fullmatch(r"\d{6}", code or ""):
        return False
    return bool(pyotp.TOTP(secret).verify(code, valid_window=1))


def hash_api_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def identifier_hash(value: str) -> str:
    material = f"{settings.secret_key}:{value}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def credit_cost(query_type: str) -> int:
    if query_type in LOCAL_MODULES or query_type in {"ambiguous_numeric", "rejected"}:
        return 0
    if query_type in EXTERNAL_MODULES or query_type == "universal":
        return 1
    return 1


def permissions_for(role: str, auth: str = "jwt", scopes: set[str] | None = None) -> set[str]:
    base = set(ROLE_PERMISSIONS.get(role, set()))
    if auth == "api_key":
        return base & (scopes or set())
    return base


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "org")[:48]


def validate_purpose(purpose: str, lawful_basis: str) -> str | None:
    if not purpose or len(purpose.strip()) < 8:
        return "A purpose of at least 8 characters is required"
    if len(purpose) > 500:
        return "Purpose is too long"
    if lawful_basis not in LAWFUL_BASES:
        return "lawful_basis must be one of: " + ", ".join(sorted(LAWFUL_BASES))
    return None


@dataclass
class Principal:
    user_id: uuid.UUID | None
    org_id: uuid.UUID
    role: str
    auth: str
    email: str | None = None
    full_name: str | None = None
    is_fixture: bool = False
    scopes: set[str] = field(default_factory=set)
    api_key_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None

    def allows(self, permission: str) -> bool:
        return permission in permissions_for(self.role, self.auth, self.scopes)
