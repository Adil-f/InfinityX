"""Local-first API authentication for protected InfinityX routes.

Connection read/disconnect require a shared app API token (not Meta OAuth).
OAuth start/callback stay public by design; Meta CSRF is handled via oauth `state`.

Clients must send:
  Authorization: Bearer <APP_API_TOKEN>
or:
  X-InfinityX-Token: <APP_API_TOKEN>

The token is a local operator secret (env). It is not an Instagram User access token
and must never be confused with Meta tokens. Browser clients load it from
VITE_APP_API_TOKEN; MCP/agents use the same env value. Bearer auth avoids relying
on cookies, so classic cross-site cookie CSRF does not apply.
"""

from __future__ import annotations

import hmac

from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings

API_TOKEN_HEADER = "X-InfinityX-Token"


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def require_app_api_token(
    authorization: str | None = Header(default=None),
    x_infinityx_token: str | None = Header(default=None, alias=API_TOKEN_HEADER),
    settings: Settings = Depends(get_settings),
) -> str:
    """FastAPI dependency: reject callers that lack a valid APP_API_TOKEN."""
    expected = (settings.app_api_token or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "APP_API_TOKEN is not configured. Set it in the backend environment "
                "before reading or changing Instagram connection state."
            ),
        )

    provided = _extract_bearer(authorization) or (x_infinityx_token or "").strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid APP_API_TOKEN required (Authorization: Bearer … or X-InfinityX-Token).",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return provided
