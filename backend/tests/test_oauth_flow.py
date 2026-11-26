from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.crypto import TokenEncryptor
from app.db import get_engine
from app.meta_client import InstagramProfile, LongLivedToken, ShortLivedToken
from app.models import InstagramAccount, OAuthState, OAuthToken
from app.oauth_service import complete_oauth
from sqlalchemy.orm import Session, sessionmaker


def test_health(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["meta_configured"] is True


def test_connection_false_without_tokens(client: TestClient):
    res = client.get("/api/instagram/connection")
    assert res.status_code == 200
    body = res.json()
    assert body["connected"] is False
    assert body["account"] is None
    assert "No Instagram account connected" in (body.get("message") or "")


def test_oauth_start_redirect_and_state(client: TestClient):
    res = client.get("/api/oauth/instagram/start", follow_redirects=False)
    assert res.status_code == 302
    location = res.headers["location"]
    assert location.startswith("https://www.instagram.com/oauth/authorize?")
    qs = parse_qs(urlparse(location).query)
    assert qs["client_id"] == ["test-app-id"]
    assert qs["response_type"] == ["code"]
    assert "instagram_business_basic" in qs["scope"][0]
    state = qs["state"][0]

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        row = session.get(OAuthState, state)
        assert row is not None
        assert row.consumed is False


def test_oauth_start_json(client: TestClient):
    res = client.get("/api/oauth/instagram/start?format=json")
    assert res.status_code == 200
    body = res.json()
    assert "authorize_url" in body
    assert "instagram.com/oauth/authorize" in body["authorize_url"]


def test_callback_rejects_bad_state(client: TestClient):
    res = client.get(
        "/api/oauth/instagram/callback",
        params={"code": "AQBx", "state": "not-a-real-state"},
        follow_redirects=False,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_complete_oauth_stores_encrypted_token(client: TestClient, encryption_key: str):
    # `client` fixture initializes the shared in-memory schema
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    encryptor = TokenEncryptor(encryption_key)

    mock_client = AsyncMock()
    mock_client.exchange_code.return_value = ShortLivedToken(
        access_token="short-lived",
        user_id="1020999",
        permissions=["instagram_business_basic", "instagram_business_manage_insights"],
    )
    mock_client.exchange_long_lived.return_value = LongLivedToken(
        access_token="long-lived-secret-token",
        token_type="bearer",
        expires_in=5184000,
    )
    mock_client.get_profile.return_value = InstagramProfile(
        id="scoped",
        user_id="1020999",
        username="real_creator",
        name="Real Creator",
        account_type="Media_Creator",
    )

    from app.config import get_settings

    settings = get_settings()
    with SessionLocal() as session:
        account = await complete_oauth(
            session=session,
            settings=settings,
            encryptor=encryptor,
            code="AQBx-code",
            client=mock_client,
        )
        session.commit()
        assert account.ig_user_id == "1020999"
        assert account.username == "real_creator"
        assert account.account_type == "Media_Creator"
        assert account.token is not None
        assert account.token.access_token_encrypted != "long-lived-secret-token"
        assert encryptor.decrypt(account.token.access_token_encrypted) == "long-lived-secret-token"
        assert "instagram_business_basic" in (account.permissions or "")


def test_callback_happy_path_mocked(client: TestClient, encryption_key: str):
    # Create a valid state first
    start = client.get("/api/oauth/instagram/start?format=json")
    state = start.json()["state"]

    async def fake_complete_oauth(**kwargs):
        session: Session = kwargs["session"]
        encryptor: TokenEncryptor = kwargs["encryptor"]
        now = datetime.now(timezone.utc)
        account = InstagramAccount(
            ig_user_id="555",
            username="linked_user",
            name="Linked",
            account_type="Business",
            permissions="instagram_business_basic",
            is_active=True,
            connected_at=now,
            updated_at=now,
        )
        session.add(account)
        session.flush()
        account.token = OAuthToken(
            access_token_encrypted=encryptor.encrypt("live-token-value"),
            token_type="bearer",
            expires_at=now + timedelta(days=60),
            obtained_at=now,
        )
        session.flush()
        return account

    with patch("app.routes.oauth.complete_oauth", new=AsyncMock(side_effect=fake_complete_oauth)):
        res = client.get(
            "/api/oauth/instagram/callback",
            params={"code": "AQBx-real", "state": state},
            follow_redirects=False,
        )
    assert res.status_code == 302
    assert "connected=true" in res.headers["location"]

    status = client.get("/api/instagram/connection")
    assert status.status_code == 200
    body = status.json()
    assert body["connected"] is True
    assert body["account"]["username"] == "linked_user"
    assert body["account"]["ig_user_id"] == "555"
    # Never expose raw tokens
    assert "access_token" not in status.text
    assert "live-token-value" not in status.text


def test_disconnect(client: TestClient, encryption_key: str):
    # Uses client fixture so schema exists on the shared engine
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    encryptor = TokenEncryptor(encryption_key)
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        account = InstagramAccount(
            ig_user_id="777",
            username="to_disconnect",
            is_active=True,
            connected_at=now,
            permissions="instagram_business_basic",
        )
        session.add(account)
        session.flush()
        account.token = OAuthToken(
            access_token_encrypted=encryptor.encrypt("tok"),
            expires_at=now + timedelta(days=30),
            obtained_at=now,
        )
        session.commit()

    before = client.get("/api/instagram/connection").json()
    assert before["connected"] is True

    deleted = client.delete("/api/instagram/connection")
    assert deleted.status_code == 200
    assert deleted.json()["connected"] is False

    after = client.get("/api/instagram/connection").json()
    assert after["connected"] is False


def test_start_requires_config(monkeypatch):
    monkeypatch.setenv("META_INSTAGRAM_APP_ID", "")
    monkeypatch.setenv("META_INSTAGRAM_APP_SECRET", "")
    from app.config import get_settings
    from app.db import reset_engine
    from app.main import app

    get_settings.cache_clear()
    reset_engine()
    with TestClient(app) as c:
        res = c.get("/api/oauth/instagram/start?format=json")
        assert res.status_code == 503
    get_settings.cache_clear()
