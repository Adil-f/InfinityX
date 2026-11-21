from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str = "dev-only-change-me-not-for-production"
    access_token_minutes: int = 30
    database_url: str = "postgresql+psycopg://infinityx:infinityx@127.0.0.1:5432/infinityx"
    redis_url: str = "redis://127.0.0.1:6379/0"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    seed_dev_fixtures: bool = False
    admin_email: str = "admin@infinityx.local"
    admin_password: str = "ChangeMe-Local-Only-1"
    admin_name: str = "Local Admin"
    hibp_api_key: str | None = None
    virustotal_api_key: str | None = None
    otx_api_key: str | None = None
    github_token: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_pro: str | None = None
    stripe_price_enterprise: str | None = None
    authorized_identity_provider_url: str | None = None
    authorized_identity_provider_token: str | None = None
    public_app_url: str = "http://localhost:3000"

    @field_validator(
        "hibp_api_key",
        "virustotal_api_key",
        "otx_api_key",
        "github_token",
        "stripe_secret_key",
        "stripe_webhook_secret",
        "stripe_price_pro",
        "stripe_price_enterprise",
        "authorized_identity_provider_url",
        "authorized_identity_provider_token",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def validate_runtime(current: Settings) -> None:
    if current.app_env != "production":
        return
    if current.secret_key.startswith("dev-only") or len(current.secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be a unique production secret of at least 32 characters")
    if current.seed_dev_fixtures:
        raise RuntimeError("SEED_DEV_FIXTURES must be false in production")
