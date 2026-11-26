"""Auth + CORS expectations for connection endpoints (security review HIGH)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.crypto import TokenEncryptor
from app.db import get_engine
from app.models import InstagramAccount, OAuthToken
from sqlalchemy.orm import sessionmaker


def _seed_connected(encryption_key: str) -> None:
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    encryptor = TokenEncryptor(encryption_key)
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        account = InstagramAccount(
            ig_user_id="999",
            username="secured_user",
            name="Secured",
            account_type="Media_Creator",
            permissions="instagram_business_basic",
            is_active=True,
            connected_at=now,
        )
        session.add(account)
        session.flush()
        account.token = OAuthToken(
            access_token_encrypted=encryptor.encrypt("secret-ig-token"),
            expires_at=now + timedelta(days=30),
            obtained_at=now,
        )
        session.commit()


def test_connection_get_unauthorized_without_token(client: TestClient, encryption_key: str):
    _seed_connected(encryption_key)
    res = client.get("/api/instagram/connection")
    assert res.status_code == 401
    assert "secured_user" not in res.text
    assert "secret-ig-token" not in res.text


def test_connection_get_rejects_wrong_token(client: TestClient, encryption_key: str):
    _seed_connected(encryption_key)
    res = client.get(
        "/api/instagram/connection",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert res.status_code == 401


def test_connection_delete_unauthorized_cannot_wipe(
    client: TestClient, encryption_key: str, auth_headers: dict[str, str]
):
    _seed_connected(encryption_key)
    res = client.delete("/api/instagram/connection")
    assert res.status_code == 401

    # Grant still present when authorized read follows
    ok = client.get("/api/instagram/connection", headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json()["connected"] is True
    assert ok.json()["account"]["username"] == "secured_user"


def test_connection_accepts_x_infinityx_token_header(
    client: TestClient, encryption_key: str, api_token: str
):
    _seed_connected(encryption_key)
    res = client.get(
        "/api/instagram/connection",
        headers={"X-InfinityX-Token": api_token},
    )
    assert res.status_code == 200
    assert res.json()["connected"] is True


def test_oauth_routes_remain_public(client: TestClient):
    # Start does not require APP_API_TOKEN
    res = client.get("/api/oauth/instagram/start?format=json")
    assert res.status_code == 200
    assert "authorize_url" in res.json()


def test_cors_allows_configured_origin(client: TestClient, auth_headers: dict[str, str]):
    res = client.get(
        "/api/instagram/connection",
        headers={**auth_headers, "Origin": "http://localhost:5173"},
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-credentials" not in {
        k.lower() for k in res.headers.keys()
    }


def test_cors_rejects_unknown_origin_preflight(client: TestClient):
    res = client.options(
        "/api/instagram/connection",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert res.status_code == 403
    assert res.headers.get("access-control-allow-origin") is None


def test_cors_preflight_ok_for_allowed_origin(client: TestClient):
    res = client.options(
        "/api/instagram/connection",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert res.status_code == 204
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    allow_headers = (res.headers.get("access-control-allow-headers") or "").lower()
    assert "authorization" in allow_headers
    assert "x-infinityx-token" in allow_headers


def test_cors_never_reflects_star(client: TestClient, auth_headers: dict[str, str]):
    res = client.get(
        "/api/instagram/connection",
        headers={**auth_headers, "Origin": "http://localhost:5173"},
    )
    assert res.headers.get("access-control-allow-origin") != "*"
