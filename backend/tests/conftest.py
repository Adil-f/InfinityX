import os

os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-please-change-32bytes-min"
os.environ["DATABASE_URL"] = "postgresql+psycopg://infinityx:infinityx@127.0.0.1:5432/infinityx_test"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/15"
os.environ["SEED_DEV_FIXTURES"] = "false"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["HIBP_API_KEY"] = ""
os.environ["VIRUSTOTAL_API_KEY"] = ""
os.environ["OTX_API_KEY"] = ""
os.environ["STRIPE_SECRET_KEY"] = ""
os.environ["STRIPE_WEBHOOK_SECRET"] = ""
os.environ["AUTHORIZED_IDENTITY_PROVIDER_URL"] = ""
os.environ["AUTHORIZED_IDENTITY_PROVIDER_TOKEN"] = ""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
