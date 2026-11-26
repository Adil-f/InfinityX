from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AccountInfo(BaseModel):
    ig_user_id: str
    username: str | None = None
    name: str | None = None
    account_type: str | None = None
    permissions: list[str] = Field(default_factory=list)
    connected_at: datetime | None = None
    token_expires_at: datetime | None = None


class ConnectionStatus(BaseModel):
    """Connection status derived only from real stored OAuth tokens."""

    connected: bool
    account: AccountInfo | None = None
    meta_configured: bool = False
    message: str | None = None


class OAuthStartResponse(BaseModel):
    authorize_url: str
    state: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    meta_configured: bool
