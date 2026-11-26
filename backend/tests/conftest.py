from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

TEST_KEY = Fernet.generate_key().decode()

os.environ.setdefault("TOKEN_ENCRYPTION_KEY", TEST_KEY)
os.environ["TOKEN_ENCRYPTION_KEY"] = TEST_KEY
os.environ["META_INSTAGRAM_APP_ID"] = "test-app-id"
os.environ["META_INSTAGRAM_APP_SECRET"] = "test-app-secret"
os.environ["META_OAUTH_REDIRECT_URI"] = "http://testserver/api/oauth/instagram/callback"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FRONTEND_SUCCESS_URL"] = "http://localhost:5173/"
os.environ["OAUTH_SCOPES"] = (
    "instagram_business_basic,instagram_business_manage_insights,instagram_business_manage_comments"
)

from app.config import get_settings  # noqa: E402
from app.db import Base, get_engine, init_db, reset_engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    os.environ["TOKEN_ENCRYPTION_KEY"] = TEST_KEY
    os.environ["META_INSTAGRAM_APP_ID"] = "test-app-id"
    os.environ["META_INSTAGRAM_APP_SECRET"] = "test-app-secret"
    os.environ["META_OAUTH_REDIRECT_URI"] = "http://testserver/api/oauth/instagram/callback"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    get_settings.cache_clear()
    reset_engine()
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    reset_engine()
    get_settings.cache_clear()
    app.dependency_overrides = {}


@pytest.fixture
def encryption_key() -> str:
    return TEST_KEY
