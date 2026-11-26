from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.crypto import TokenEncryptor, encryptor_from_settings
from app.db import get_session
from app.oauth_service import build_start_url, complete_oauth, consume_oauth_state
from app.schemas import OAuthStartResponse

router = APIRouter(prefix="/api/oauth/instagram", tags=["oauth"])


def _settings() -> Settings:
    return get_settings()


def _encryptor(settings: Settings = Depends(_settings)) -> TokenEncryptor:
    try:
        return encryptor_from_settings(settings)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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
                "META_INSTAGRAM_APP_SECRET, META_OAUTH_REDIRECT_URI, and TOKEN_ENCRYPTION_KEY."
            ),
        )
    try:
        authorize_url = build_start_url(session, settings)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    wants_json = format == "json" or "application/json" in (
        request.headers.get("accept") or ""
    )
    if wants_json:
        # state is embedded in the authorize URL; extract for clients that need it
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
    encryptor: TokenEncryptor = Depends(_encryptor),
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
        raise HTTPException(status_code=400, detail="Missing authorization code")

    if not consume_oauth_state(session, state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if not settings.meta_configured:
        raise HTTPException(status_code=503, detail="Meta Instagram OAuth is not configured")

    try:
        account = await complete_oauth(
            session=session,
            settings=settings,
            encryptor=encryptor,
            code=code,
        )
    except Exception as exc:
        qs = urlencode({"connected": "false", "error": "oauth_failed", "error_description": str(exc)})
        return RedirectResponse(url=f"{frontend}?{qs}", status_code=302)

    qs = urlencode(
        {
            "connected": "true",
            "username": account.username or "",
            "ig_user_id": account.ig_user_id,
        }
    )
    return RedirectResponse(url=f"{frontend}?{qs}", status_code=302)
