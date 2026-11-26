"""Regression coverage for gaps listed in docs/pr-5-review.md."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.crypto import TokenEncryptor
from app.db import get_engine
from app.meta_client import InstagramProfile, LongLivedToken, MetaInstagramError, ShortLivedToken
from app.models import InstagramAccount, OAuthState, OAuthToken
from app.oauth_service import complete_oauth, get_active_connection


def test_expired_oauth_state_rejected(client: TestClient):
    start = client.get("/api/oauth/instagram/start?format=json")
    state = start.json()["state"]

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        row = session.get(OAuthState, state)
        assert row is not None
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()

    res = client.get(
        "/api/oauth/instagram/callback",
        params={"code": "AQBx-expired", "state": state},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "invalid_state" in res.headers["location"]
    assert "connected=false" in res.headers["location"]


def test_replayed_oauth_state_rejected(client: TestClient, auth_headers: dict[str, str]):
    start = client.get("/api/oauth/instagram/start?format=json")
    state = start.json()["state"]

    async def fake_complete_oauth(**kwargs):
        session = kwargs["session"]
        encryptor: TokenEncryptor = kwargs["encryptor"]
        now = datetime.now(timezone.utc)
        account = InstagramAccount(
            ig_user_id="444",
            username="first_ok",
            permissions="instagram_business_basic",
            is_active=True,
            connected_at=now,
            updated_at=now,
        )
        session.add(account)
        session.flush()
        account.token = OAuthToken(
            access_token_encrypted=encryptor.encrypt("first-token"),
            token_type="bearer",
            expires_at=now + timedelta(days=60),
            obtained_at=now,
        )
        session.flush()
        return account

    with patch("app.routes.oauth.complete_oauth", new=AsyncMock(side_effect=fake_complete_oauth)):
        first = client.get(
            "/api/oauth/instagram/callback",
            params={"code": "AQBx-first", "state": state},
            follow_redirects=False,
        )
    assert first.status_code == 302
    assert "connected=true" in first.headers["location"]

    second = client.get(
        "/api/oauth/instagram/callback",
        params={"code": "AQBx-replay", "state": state},
        follow_redirects=False,
    )
    assert second.status_code == 302
    assert "invalid_state" in second.headers["location"]
    assert "connected=false" in second.headers["location"]


def test_callback_meta_error_redirects(client: TestClient, auth_headers: dict[str, str]):
    res = client.get(
        "/api/oauth/instagram/callback",
        params={
            "error": "access_denied",
            "error_reason": "user_denied",
            "error_description": "The+user+denied+your+request",
        },
        follow_redirects=False,
    )
    assert res.status_code == 302
    location = res.headers["location"]
    assert "connected=false" in location
    assert "access_denied" in location
    assert "user_denied" in location

    status = client.get("/api/instagram/connection", headers=auth_headers)
    assert status.json()["connected"] is False


def test_callback_missing_code_redirects(client: TestClient, auth_headers: dict[str, str]):
    start = client.get("/api/oauth/instagram/start?format=json")
    state = start.json()["state"]
    res = client.get(
        "/api/oauth/instagram/callback",
        params={"state": state},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "missing_code" in res.headers["location"]
    assert "connected=false" in res.headers["location"]

    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        row = session.get(OAuthState, state)
        assert row is not None
        assert row.consumed is False


def test_missing_app_api_token_returns_503(monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "")
    get_settings.cache_clear()
    from app.db import reset_engine
    from app.main import app
    from tests.conftest import TEST_API_TOKEN, TEST_KEY

    reset_engine()
    with TestClient(app) as client:
        res = client.get("/api/instagram/connection")
        assert res.status_code == 503
        assert "APP_API_TOKEN" in res.json()["detail"]

    monkeypatch.setenv("APP_API_TOKEN", TEST_API_TOKEN)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", TEST_KEY)
    get_settings.cache_clear()


def test_cors_rejects_unauthorized_non_preflight(client: TestClient, auth_headers: dict[str, str]):
    res = client.get(
        "/api/instagram/connection",
        headers={**auth_headers, "Origin": "https://evil.example"},
    )
    assert res.status_code == 403
    assert res.headers.get("access-control-allow-origin") is None
    assert "secured_user" not in res.text


def test_cors_star_origin_dropped_from_allowlist(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*,http://localhost:5173")
    get_settings.cache_clear()
    settings = get_settings()
    assert "*" not in settings.cors_origin_list
    assert "http://localhost:5173" in settings.cors_origin_list
    from tests.conftest import TEST_API_TOKEN, TEST_KEY

    monkeypatch.setenv("APP_API_TOKEN", TEST_API_TOKEN)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", TEST_KEY)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_profile_failure_does_not_persist_grant(client: TestClient, encryption_key: str):
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    encryptor = TokenEncryptor(encryption_key)

    mock_client = AsyncMock()
    mock_client.exchange_code.return_value = ShortLivedToken(
        access_token="short-lived-plaintext",
        user_id="333",
        permissions=["instagram_business_basic"],
    )
    mock_client.exchange_long_lived.return_value = LongLivedToken(
        access_token="long-lived-plaintext",
        token_type="bearer",
        expires_in=5184000,
    )
    mock_client.get_profile.side_effect = MetaInstagramError(
        "Failed to fetch Instagram profile",
        status_code=400,
    )

    settings = get_settings()
    with SessionLocal() as session:
        with pytest.raises(MetaInstagramError):
            await complete_oauth(
                session=session,
                settings=settings,
                encryptor=encryptor,
                code="AQBx-profile-fail",
                client=mock_client,
            )
        session.rollback()

    with SessionLocal() as session:
        assert get_active_connection(session) is None
        accounts = session.scalars(select(InstagramAccount)).all()
        assert accounts == []
        tokens = session.scalars(select(OAuthToken)).all()
        assert tokens == []


def test_callback_profile_failure_redirects_without_grant(
    client: TestClient, auth_headers: dict[str, str]
):
    start = client.get("/api/oauth/instagram/start?format=json")
    state = start.json()["state"]

    async def failing_complete_oauth(**_kwargs):
        raise MetaInstagramError("Failed to fetch Instagram profile", status_code=400)

    with patch(
        "app.routes.oauth.complete_oauth",
        new=AsyncMock(side_effect=failing_complete_oauth),
    ):
        res = client.get(
            "/api/oauth/instagram/callback",
            params={"code": "AQBx-no-profile", "state": state},
            follow_redirects=False,
        )
    assert res.status_code == 302
    assert "connected=false" in res.headers["location"]
    assert "oauth_failed" in res.headers["location"]

    status = client.get("/api/instagram/connection", headers=auth_headers)
    assert status.status_code == 200
    assert status.json()["connected"] is False


@pytest.mark.asyncio
async def test_successful_exchange_does_not_store_short_lived_plaintext(
    client: TestClient, encryption_key: str
):
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    encryptor = TokenEncryptor(encryption_key)

    short_plain = "SHORT_LIVED_PLAINTEXT_MARKER"
    long_plain = "LONG_LIVED_PLAINTEXT_MARKER"

    mock_client = AsyncMock()
    mock_client.exchange_code.return_value = ShortLivedToken(
        access_token=short_plain,
        user_id="5555",
        permissions=["instagram_business_basic"],
    )
    mock_client.exchange_long_lived.return_value = LongLivedToken(
        access_token=long_plain,
        token_type="bearer",
        expires_in=5184000,
    )
    mock_client.get_profile.return_value = InstagramProfile(
        id="scoped",
        user_id="5555",
        username="plain_check",
        name="Plain",
        account_type="Media_Creator",
    )

    settings = get_settings()
    with SessionLocal() as session:
        account = await complete_oauth(
            session=session,
            settings=settings,
            encryptor=encryptor,
            code="AQBx-plain",
            client=mock_client,
        )
        session.commit()
        assert account.token is not None
        cipher = account.token.access_token_encrypted
        assert short_plain not in cipher
        assert long_plain not in cipher
        assert encryptor.decrypt(cipher) == long_plain

        # Raw short-lived string must not appear anywhere in token table
        raw_rows = session.scalars(select(OAuthToken.access_token_encrypted)).all()
        blob = "|".join(raw_rows)
        assert short_plain not in blob
        assert long_plain not in blob
