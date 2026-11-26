"""Regression tests for Bugbot Medium findings on PR #5."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.crypto import TokenEncryptor
from app.db import get_engine
from app.meta_client import InstagramProfile, LongLivedToken, ShortLivedToken
from app.models import InstagramAccount, OAuthToken
from app.oauth_service import complete_oauth, disconnect_active, get_active_connection


def test_invalid_encryption_key_blocks_oauth_start(monkeypatch):
    """meta_configured must reject non-Fernet TOKEN_ENCRYPTION_KEY before Meta redirect."""
    monkeypatch.setenv("META_INSTAGRAM_APP_ID", "test-app-id")
    monkeypatch.setenv("META_INSTAGRAM_APP_SECRET", "test-app-secret")
    monkeypatch.setenv(
        "META_OAUTH_REDIRECT_URI", "http://testserver/api/oauth/instagram/callback"
    )
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "not-valid-fernet-material")
    monkeypatch.setenv("APP_API_TOKEN", "test-local-app-api-token-not-meta")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.token_encryption_key.strip() != ""
    assert settings.meta_configured is False

    from app.db import reset_engine
    from app.main import app

    reset_engine()
    with TestClient(app) as client:
        res = client.get("/api/oauth/instagram/start?format=json")
        assert res.status_code == 503
        assert "TOKEN_ENCRYPTION_KEY" in res.json()["detail"] or "Fernet" in res.json()["detail"] or "not configured" in res.json()["detail"].lower()

    # Restore valid key for other tests / fixture
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
    get_settings.cache_clear()


def test_callback_redirects_on_invalid_encryption_key(client: TestClient, monkeypatch):
    """Callback must not return a raw 503; redirect to frontend failure URL."""
    from tests.conftest import TEST_KEY

    start = client.get("/api/oauth/instagram/start?format=json")
    state = start.json()["state"]

    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "still-not-a-fernet-key")
    get_settings.cache_clear()

    res = client.get(
        "/api/oauth/instagram/callback",
        params={"code": "AQBx-after-meta", "state": state},
        follow_redirects=False,
    )
    assert res.status_code == 302
    location = res.headers["location"]
    assert "connected=false" in location
    assert (
        "encryption_misconfigured" in location
        or "oauth_failed" in location
        or "not_configured" in location
    )
    assert location.startswith("http://localhost:5173")

    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", TEST_KEY)
    get_settings.cache_clear()


def test_oauth_state_not_burned_on_encryption_config_failure(
    client: TestClient, monkeypatch, auth_headers: dict[str, str]
):
    """Config/encrypt failure must leave OAuth state reusable after fixing the key."""
    from unittest.mock import AsyncMock, patch

    from tests.conftest import TEST_KEY

    from app.db import get_engine
    from app.models import OAuthState
    from sqlalchemy.orm import sessionmaker

    start = client.get("/api/oauth/instagram/start?format=json")
    state = start.json()["state"]

    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "not-valid-fernet-material")
    get_settings.cache_clear()

    failed = client.get(
        "/api/oauth/instagram/callback",
        params={"code": "AQBx-retryable", "state": state},
        follow_redirects=False,
    )
    assert failed.status_code == 302
    assert "encryption_misconfigured" in failed.headers["location"] or "not_configured" in failed.headers["location"]

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        row = session.get(OAuthState, state)
        assert row is not None
        assert row.consumed is False

    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", TEST_KEY)
    get_settings.cache_clear()

    async def fake_complete_oauth(**kwargs):
        from datetime import datetime, timedelta, timezone

        from app.crypto import TokenEncryptor
        from app.models import InstagramAccount, OAuthToken

        session = kwargs["session"]
        encryptor: TokenEncryptor = kwargs["encryptor"]
        now = datetime.now(timezone.utc)
        account = InstagramAccount(
            ig_user_id="888",
            username="retry_user",
            permissions="instagram_business_basic",
            is_active=True,
            connected_at=now,
            updated_at=now,
        )
        session.add(account)
        session.flush()
        account.token = OAuthToken(
            access_token_encrypted=encryptor.encrypt("retry-token"),
            token_type="bearer",
            expires_at=now + timedelta(days=60),
            obtained_at=now,
        )
        session.flush()
        return account

    with patch("app.routes.oauth.complete_oauth", new=AsyncMock(side_effect=fake_complete_oauth)):
        ok = client.get(
            "/api/oauth/instagram/callback",
            params={"code": "AQBx-retryable", "state": state},
            follow_redirects=False,
        )
    assert ok.status_code == 302
    assert "connected=true" in ok.headers["location"]

    status = client.get("/api/instagram/connection", headers=auth_headers)
    assert status.status_code == 200
    assert status.json()["connected"] is True
    assert status.json()["account"]["username"] == "retry_user"

    with SessionLocal() as session:
        row = session.get(OAuthState, state)
        assert row is not None
        assert row.consumed is True


@pytest.mark.asyncio
async def test_reconnect_deactivates_prior_account(client: TestClient, encryption_key: str):
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    encryptor = TokenEncryptor(encryption_key)
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        prior = InstagramAccount(
            ig_user_id="111",
            username="old_creator",
            permissions="instagram_business_basic",
            is_active=True,
            connected_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
        )
        session.add(prior)
        session.flush()
        prior.token = OAuthToken(
            access_token_encrypted=encryptor.encrypt("old-token"),
            expires_at=now + timedelta(days=30),
            obtained_at=now - timedelta(days=1),
        )
        session.commit()
        prior_id = prior.id

    mock_client = AsyncMock()
    mock_client.exchange_code.return_value = ShortLivedToken(
        access_token="short",
        user_id="222",
        permissions=["instagram_business_basic"],
    )
    mock_client.exchange_long_lived.return_value = LongLivedToken(
        access_token="new-long-token",
        token_type="bearer",
        expires_in=5184000,
    )
    mock_client.get_profile.return_value = InstagramProfile(
        id="scoped-2",
        user_id="222",
        username="new_creator",
        name="New",
        account_type="Media_Creator",
    )

    settings = get_settings()
    with SessionLocal() as session:
        account = await complete_oauth(
            session=session,
            settings=settings,
            encryptor=encryptor,
            code="AQBx",
            client=mock_client,
        )
        session.commit()
        assert account.ig_user_id == "222"
        assert account.is_active is True

        prior_row = session.get(InstagramAccount, prior_id)
        assert prior_row is not None
        assert prior_row.is_active is False
        assert prior_row.token is None

        active = get_active_connection(session)
        assert active is not None
        assert active.ig_user_id == "222"

        # Only one active account
        active_count = len(
            session.scalars(
                select(InstagramAccount).where(InstagramAccount.is_active.is_(True))
            ).all()
        )
        assert active_count == 1

        disconnect_active(session)
        session.commit()
        assert get_active_connection(session) is None
