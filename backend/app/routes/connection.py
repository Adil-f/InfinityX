from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.oauth_service import disconnect_active, get_active_connection
from app.schemas import AccountInfo, ConnectionStatus

router = APIRouter(prefix="/api/instagram", tags=["instagram"])


@router.get("/connection", response_model=ConnectionStatus)
def connection_status(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ConnectionStatus:
    """Report connection only when a real encrypted token exists in SQLite."""
    account = get_active_connection(session)
    if account is None or account.token is None:
        return ConnectionStatus(
            connected=False,
            meta_configured=settings.meta_configured,
            message=(
                "No Instagram account connected via Meta OAuth."
                if settings.meta_configured
                else "Meta App credentials not configured; live OAuth cannot start yet."
            ),
        )

    permissions = [
        p.strip() for p in (account.permissions or "").split(",") if p.strip()
    ]
    return ConnectionStatus(
        connected=True,
        meta_configured=settings.meta_configured,
        account=AccountInfo(
            ig_user_id=account.ig_user_id,
            username=account.username,
            name=account.name,
            account_type=account.account_type,
            permissions=permissions,
            connected_at=account.connected_at,
            token_expires_at=account.token.expires_at if account.token else None,
        ),
    )


@router.delete("/connection", response_model=ConnectionStatus)
def disconnect(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ConnectionStatus:
    disconnect_active(session)
    return ConnectionStatus(
        connected=False,
        meta_configured=settings.meta_configured,
        message="Instagram connection cleared.",
    )
