"""OAuth state management and token persistence."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.crypto import TokenEncryptor
from app.meta_client import (
    InstagramProfile,
    LongLivedToken,
    MetaInstagramClient,
    MetaInstagramError,
    ShortLivedToken,
    build_authorize_url,
)
from app.models import InstagramAccount, OAuthState, OAuthToken


def create_oauth_state(session: Session, settings: Settings) -> str:
    state = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    row = OAuthState(
        state=state,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.oauth_state_ttl_seconds),
        consumed=False,
    )
    session.add(row)
    session.flush()
    return state


def consume_oauth_state(session: Session, state: str | None) -> bool:
    if not state:
        return False
    row = session.get(OAuthState, state)
    if row is None or row.consumed:
        return False
    now = datetime.now(timezone.utc)
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        return False
    row.consumed = True
    session.flush()
    return True


def build_start_url(session: Session, settings: Settings) -> str:
    if not settings.meta_instagram_app_id or not settings.meta_oauth_redirect_uri:
        raise ValueError("Meta Instagram App ID and redirect URI must be configured")
    state = create_oauth_state(session, settings)
    return build_authorize_url(
        client_id=settings.meta_instagram_app_id,
        redirect_uri=settings.meta_oauth_redirect_uri,
        scopes=settings.scope_list,
        state=state,
    )


async def complete_oauth(
    *,
    session: Session,
    settings: Settings,
    encryptor: TokenEncryptor,
    code: str,
    client: MetaInstagramClient | None = None,
) -> InstagramAccount:
    owns_client = client is None
    meta = client or MetaInstagramClient(
        client_id=settings.meta_instagram_app_id,
        client_secret=settings.meta_instagram_app_secret,
        redirect_uri=settings.meta_oauth_redirect_uri,
    )
    try:
        if owns_client:
            await meta.__aenter__()
        short: ShortLivedToken = await meta.exchange_code(code)
        long: LongLivedToken = await meta.exchange_long_lived(short.access_token)
        # /me must succeed before any grant is stored or activated.
        profile: InstagramProfile = await meta.get_profile(long.access_token)
    finally:
        if owns_client:
            await meta.__aexit__(None, None, None)

    if not profile.user_id and not short.user_id:
        raise MetaInstagramError("Instagram profile response missing user identity")

    permissions = short.permissions or settings.scope_list
    permissions_str = ",".join(permissions)
    # Prefer Graph user_id when present; fall back to token-exchange user_id
    ig_user_id = profile.user_id or short.user_id

    account = session.scalar(
        select(InstagramAccount).where(InstagramAccount.ig_user_id == ig_user_id)
    )
    now = datetime.now(timezone.utc)
    if account is None:
        account = InstagramAccount(
            ig_user_id=ig_user_id,
            username=profile.username,
            name=profile.name,
            account_type=profile.account_type,
            permissions=permissions_str,
            is_active=True,
            connected_at=now,
            updated_at=now,
        )
        session.add(account)
        session.flush()
    else:
        account.username = profile.username or account.username
        account.name = profile.name or account.name
        account.account_type = profile.account_type or account.account_type
        account.permissions = permissions_str
        account.is_active = True
        account.updated_at = now
        account.connected_at = now

    encrypted = encryptor.encrypt(long.access_token)
    expires_at = now + timedelta(seconds=long.expires_in)

    if account.token is None:
        account.token = OAuthToken(
            access_token_encrypted=encrypted,
            token_type=long.token_type,
            expires_at=expires_at,
            obtained_at=now,
        )
    else:
        account.token.access_token_encrypted = encrypted
        account.token.token_type = long.token_type
        account.token.expires_at = expires_at
        account.token.obtained_at = now

    # Phase 1 is single-active-grant: deactivate every other account and drop their tokens.
    _deactivate_accounts_except(session, keep_account_id=account.id, now=now)

    session.flush()
    return account


def _deactivate_accounts_except(
    session: Session,
    *,
    keep_account_id: str,
    now: datetime | None = None,
) -> None:
    stamp = now or datetime.now(timezone.utc)
    others = session.scalars(
        select(InstagramAccount).where(InstagramAccount.id != keep_account_id)
    ).all()
    for other in others:
        if not other.is_active and other.token is None:
            continue
        other.is_active = False
        # delete-orphan on relationship clears encrypted tokens for prior grants
        other.token = None
        other.updated_at = stamp


def get_active_connection(session: Session) -> InstagramAccount | None:
    return session.scalar(
        select(InstagramAccount)
        .where(InstagramAccount.is_active.is_(True))
        .order_by(InstagramAccount.connected_at.desc())
    )


def disconnect_active(session: Session) -> bool:
    """Deactivate all active grants and delete their encrypted tokens."""
    accounts = list(
        session.scalars(
            select(InstagramAccount).where(InstagramAccount.is_active.is_(True))
        ).all()
    )
    if not accounts:
        return False
    now = datetime.now(timezone.utc)
    for account in accounts:
        account.is_active = False
        account.token = None
        account.updated_at = now
    session.flush()
    return True
