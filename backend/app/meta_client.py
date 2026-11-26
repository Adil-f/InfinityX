"""Official Meta Instagram API with Instagram Login HTTP helpers.

Endpoints (Business Login for Instagram / Instagram Graph):
- Authorize: https://www.instagram.com/oauth/authorize
- Code exchange: https://api.instagram.com/oauth/access_token
- Long-lived: https://graph.instagram.com/access_token
- Refresh: https://graph.instagram.com/refresh_access_token
- Profile: https://graph.instagram.com/me
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
GRAPH_BASE = "https://graph.instagram.com"


@dataclass(frozen=True)
class ShortLivedToken:
    access_token: str
    user_id: str
    permissions: list[str]


@dataclass(frozen=True)
class LongLivedToken:
    access_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class InstagramProfile:
    id: str | None
    user_id: str | None
    username: str | None
    name: str | None
    account_type: str | None


class MetaInstagramError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def build_authorize_url(
    *,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": ",".join(scopes),
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def normalize_auth_code(code: str) -> str:
    """Strip the `#_` suffix Meta appends to redirect URIs (not part of the code)."""
    cleaned = code.strip()
    if cleaned.endswith("#_"):
        cleaned = cleaned[:-2]
    if "#" in cleaned:
        cleaned = cleaned.split("#", 1)[0]
    return cleaned


class MetaInstagramClient:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._http = http
        self._owns_http = http is None

    async def __aenter__(self) -> MetaInstagramClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_http and self._http is not None:
            await self._http.aclose()

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError("HTTP client not initialized; use async with MetaInstagramClient")
        return self._http

    async def exchange_code(self, code: str) -> ShortLivedToken:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": normalize_auth_code(code),
        }
        response = await self.http.post(TOKEN_URL, data=data)
        payload = _safe_json(response)
        if response.status_code >= 400:
            raise MetaInstagramError(
                _error_message(payload, "Failed to exchange authorization code"),
                status_code=response.status_code,
                payload=payload,
            )

        # Meta may return either a flat object or {"data":[{...}]}
        item = _unwrap_token_payload(payload)
        access_token = item.get("access_token")
        user_id = str(item.get("user_id") or "")
        if not access_token or not user_id:
            raise MetaInstagramError("Token response missing access_token or user_id", payload=payload)
        permissions = _parse_permissions(item.get("permissions"))
        return ShortLivedToken(access_token=access_token, user_id=user_id, permissions=permissions)

    async def exchange_long_lived(self, short_lived_token: str) -> LongLivedToken:
        params = {
            "grant_type": "ig_exchange_token",
            "client_secret": self.client_secret,
            "access_token": short_lived_token,
        }
        response = await self.http.get(f"{GRAPH_BASE}/access_token", params=params)
        payload = _safe_json(response)
        if response.status_code >= 400:
            raise MetaInstagramError(
                _error_message(payload, "Failed to exchange long-lived token"),
                status_code=response.status_code,
                payload=payload,
            )
        access_token = payload.get("access_token")
        expires_in = int(payload.get("expires_in") or 0)
        if not access_token or not expires_in:
            raise MetaInstagramError("Long-lived token response incomplete", payload=payload)
        return LongLivedToken(
            access_token=access_token,
            token_type=str(payload.get("token_type") or "bearer"),
            expires_in=expires_in,
        )

    async def get_profile(self, access_token: str) -> InstagramProfile:
        params = {
            "fields": "id,user_id,username,name,account_type",
            "access_token": access_token,
        }
        response = await self.http.get(f"{GRAPH_BASE}/me", params=params)
        payload = _safe_json(response)
        if response.status_code >= 400:
            raise MetaInstagramError(
                _error_message(payload, "Failed to fetch Instagram profile"),
                status_code=response.status_code,
                payload=payload,
            )
        return InstagramProfile(
            id=str(payload["id"]) if payload.get("id") is not None else None,
            user_id=str(payload["user_id"]) if payload.get("user_id") is not None else None,
            username=payload.get("username"),
            name=payload.get("name"),
            account_type=payload.get("account_type"),
        )


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {"raw": response.text}
    if isinstance(data, dict):
        return data
    return {"data": data}


def _unwrap_token_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if "access_token" in payload:
        return payload
    data = payload.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    if isinstance(data, dict):
        return data
    return payload


def _parse_permissions(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(p).strip() for p in raw if str(p).strip()]
    return [p.strip() for p in str(raw).split(",") if p.strip()]


def _error_message(payload: dict[str, Any], fallback: str) -> str:
    for key in ("error_message", "error_description", "message"):
        if payload.get(key):
            return str(payload[key])
    err = payload.get("error")
    if isinstance(err, dict) and err.get("message"):
        return str(err["message"])
    if isinstance(err, str):
        return err
    return fallback
