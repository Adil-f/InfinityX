from __future__ import annotations

import re
from urllib.parse import urlparse

import ipaddress

CNIC_SEPARATED = re.compile(r"^\d{5}[-\s]\d{7}[-\s]\d$")
CNIC_BARE = re.compile(r"^\d{13}$")
EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HASH_LENGTHS = {32: "md5", 40: "sha1", 64: "sha256"}


def _host_from_url(value: str) -> str | None:
    parsed = urlparse(value)
    return parsed.hostname


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value.strip())
        return True
    except ValueError:
        return False


def normalize_domain(value: str) -> str | None:
    raw = value.strip().lower().rstrip(".")
    if "://" in raw:
        host = _host_from_url(raw)
        if not host:
            return None
        raw = host.lower().rstrip(".")
    raw = raw.split("/")[0]
    if raw.startswith("[") and "]" in raw:
        return None
    if ":" in raw:
        raw = raw.split(":")[0]
    if not raw or len(raw) > 253 or "." not in raw:
        return None
    try:
        encoded = raw.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    labels = encoded.split(".")
    if any(not label or len(label) > 63 for label in labels):
        return None
    for label in labels:
        if not re.fullmatch(r"[a-z0-9-]+", label):
            return None
        if label.startswith("-") or label.endswith("-"):
            return None
    return encoded


def is_domain(value: str) -> bool:
    return normalize_domain(value) is not None and "://" not in value.strip().lower()


def classify_query(query: str, hint: str | None = None) -> dict:
    raw = (query or "").strip()
    if hint in {"phone", "cnic", "email", "username", "social", "ip", "domain", "threat", "forensics", "url"}:
        return {"query_type": hint, "normalized": raw, "suggested_module": hint}
    if not raw:
        return {"query_type": "rejected", "normalized": "", "reason": "Query is empty", "suggested_module": None}
    if len(raw) > 512:
        return {"query_type": "rejected", "normalized": raw[:80], "reason": "Query is too long", "suggested_module": None}

    compact = re.sub(r"[\s-]", "", raw)
    if CNIC_SEPARATED.fullmatch(raw):
        return {"query_type": "cnic", "normalized": raw, "suggested_module": "cnic"}
    if raw.startswith("+") or raw.startswith("00"):
        return {"query_type": "phone", "normalized": raw, "suggested_module": "phone"}
    if EMAIL_SHAPE.fullmatch(raw):
        return {"query_type": "email", "normalized": raw.lower(), "suggested_module": "email"}
    if raw.lower().startswith("http://") or raw.lower().startswith("https://"):
        host = _host_from_url(raw)
        return {"query_type": "url", "normalized": raw, "host": host, "suggested_module": "domain"}
    if is_ip(raw):
        return {"query_type": "ip", "normalized": str(ipaddress.ip_address(raw)), "suggested_module": "ip"}
    if re.fullmatch(r"[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", raw):
        kind = HASH_LENGTHS[len(raw)]
        return {"query_type": "threat", "normalized": raw.lower(), "hash_type": kind, "suggested_module": "threat"}
    domain = normalize_domain(raw)
    if domain and " " not in raw and "/" not in raw:
        return {"query_type": "domain", "normalized": domain, "suggested_module": "domain"}
    if CNIC_BARE.fullmatch(compact) and compact == raw:
        return {
            "query_type": "ambiguous_numeric",
            "normalized": raw,
            "reason": "A 13-digit number is not automatically treated as a national identity number or a telephone number.",
            "options": ["phone", "cnic"],
            "suggested_module": None,
        }
    if re.fullmatch(r"[A-Za-z0-9._-]{2,39}", raw.lstrip("@")):
        return {"query_type": "username", "normalized": raw.lstrip("@"), "suggested_module": "username"}
    return {
        "query_type": "rejected",
        "normalized": raw[:80],
        "reason": "Query type was not recognized. Choose a module explicitly.",
        "suggested_module": None,
    }
