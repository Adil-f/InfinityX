import httpx
import pytest

from app.meta_client import (
    MetaInstagramClient,
    MetaInstagramError,
    build_authorize_url,
    normalize_auth_code,
)


def test_build_authorize_url_includes_scopes_and_state():
    url = build_authorize_url(
        client_id="123",
        redirect_uri="http://localhost/callback",
        scopes=["instagram_business_basic", "instagram_business_manage_insights"],
        state="abc",
    )
    assert url.startswith("https://www.instagram.com/oauth/authorize?")
    assert "client_id=123" in url
    assert "response_type=code" in url
    assert "state=abc" in url
    assert "instagram_business_basic" in url
    assert "instagram_business_manage_insights" in url


def test_normalize_auth_code_strips_hash():
    assert normalize_auth_code("AQBx-code#_") == "AQBx-code"
    assert normalize_auth_code("AQBx-code#frag") == "AQBx-code"


@pytest.mark.asyncio
async def test_exchange_code_flat_and_nested_payloads():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/access_token"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "access_token": "short-token",
                            "user_id": "1020",
                            "permissions": "instagram_business_basic,instagram_business_manage_comments",
                        }
                    ]
                },
            )
        raise AssertionError(f"unexpected {request.url}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = MetaInstagramClient(
            client_id="id",
            client_secret="secret",
            redirect_uri="http://localhost/callback",
            http=http,
        )
        short = await client.exchange_code("AQBx-code#_")
        assert short.access_token == "short-token"
        assert short.user_id == "1020"
        assert "instagram_business_basic" in short.permissions


@pytest.mark.asyncio
async def test_exchange_code_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error_type": "OAuthException", "error_message": "Matching code was not found"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = MetaInstagramClient(
            client_id="id",
            client_secret="secret",
            redirect_uri="http://localhost/callback",
            http=http,
        )
        with pytest.raises(MetaInstagramError) as exc:
            await client.exchange_code("bad")
        assert "Matching code" in str(exc.value)


@pytest.mark.asyncio
async def test_long_lived_and_profile():
    def handler(request: httpx.Request) -> httpx.Response:
        if "grant_type=ig_exchange_token" in str(request.url):
            return httpx.Response(
                200,
                json={"access_token": "long-token", "token_type": "bearer", "expires_in": 5184000},
            )
        if request.url.path.endswith("/me"):
            return httpx.Response(
                200,
                json={
                    "id": "ig-scoped",
                    "user_id": "1020",
                    "username": "creator_demo",
                    "name": "Creator",
                    "account_type": "Media_Creator",
                },
            )
        raise AssertionError(str(request.url))

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = MetaInstagramClient(
            client_id="id",
            client_secret="secret",
            redirect_uri="http://localhost/callback",
            http=http,
        )
        long = await client.exchange_long_lived("short")
        assert long.access_token == "long-token"
        assert long.expires_in == 5184000
        profile = await client.get_profile("long-token")
        assert profile.username == "creator_demo"
        assert profile.account_type == "Media_Creator"
