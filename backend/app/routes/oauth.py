from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.crypto import encryptor_from_settings
from app.db import get_session
from app.oauth_service import build_start_url, complete_oauth, consume_oauth_state
from app.schemas import OAuthStartResponse

router = APIRouter(prefix="/api/oauth/instagram", tags=["oauth"])


def _settings() -> Settings:
    return get_settings()


def _frontend_failure_redirect(settings: Settings, *, error: str, description: str) -> RedirectResponse:
    frontend = settings.frontend_success_url.rstrip("/") + "/"
    qs = urlencode(
        {
            "connected": "false",
            "error": error,
            "error_description": description,
        }
    )
    return RedirectResponse(url=f"{frontend}?{qs}", status_code=302)


@router.get("/start")
async def oauth_start(
    request: Request,
    format: str | None = Query(default=None, description="Set to json to return URL instead of redirect"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(_settings),
):
    if not settings.meta_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Meta Instagram OAuth is not configured. Set META_INSTAGRAM_APP_ID, "
                "META_INSTAGRAM_APP_SECRET, META_OAUTH_REDIRECT_URI, and a valid "
                "Fernet TOKEN_ENCRYPTION_KEY."
            ),
        )
    try:
        # Fail closed before sending the user to Meta if encryption is unusable.
        encryptor_from_settings(settings)
        authorize_url = build_start_url(session, settings)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    wants_json = format == "json" or "application/json" in (
        request.headers.get("accept") or ""
    )
    if wants_json:
        state = None
        if "state=" in authorize_url:
            state = authorize_url.split("state=", 1)[1].split("&", 1)[0]
        return OAuthStartResponse(authorize_url=authorize_url, state=state)
    return RedirectResponse(url=authorize_url, status_code=302)


@router.get("/callback")
async def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_reason: str | None = None,
    error_description: str | None = None,
    session: Session = Depends(get_session),
    settings: Settings = Depends(_settings),
):
    frontend = settings.frontend_success_url.rstrip("/") + "/"

    if error:
        qs = urlencode(
            {
                "connected": "false",
                "error": error,
                "error_reason": error_reason or "",
                "error_description": error_description or "Authorization was denied",
            }
        )
        return RedirectResponse(url=f"{frontend}?{qs}", status_code=302)

    if not code:
        return _frontend_failure_redirect(
            settings,
            error="missing_code",
            description="Missing authorization code",
        )

    # Validate local config/encryption BEFORE consuming OAuth state so a misconfigured
    # server does not burn Meta's one-time `code` (redirect commits would persist consume).
    try:
        encryptor = encryptor_from_settings(settings)
    except ValueError as exc:
        return _frontend_failure_redirect(
            settings,
            error="encryption_misconfigured",
            description=str(exc),
        )

    if not settings.meta_configured:
        return _frontend_failure_redirect(
            settings,
            error="not_configured",
            description="Meta Instagram OAuth is not configured",
        )

    if not consume_oauth_state(session, state):
        return _frontend_failure_redirect(
            settings,
            error="invalid_state",
            description="Invalid or expired OAuth state",
        )

    try:
        account = await complete_oauth(
            session=session,
            settings=settings,
            encryptor=encryptor,
            code=code,
        )
    except Exception as exc:
        return _frontend_failure_redirect(
            settings,
            error="oauth_failed",
            description=str(exc),
        )

    qs = urlencode(
        {
            "connected": "true",
            "username": account.username or "",
            "ig_user_id": account.ig_user_id,
        }
    )
    return RedirectResponse(url=f"{frontend}?{qs}", status_code=302)
