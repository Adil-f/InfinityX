from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_OAUTH_SCOPES = (
    "instagram_business_basic,"
    "instagram_business_manage_insights,"
    "instagram_business_manage_comments"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    meta_instagram_app_id: str = ""
    meta_instagram_app_secret: str = ""
    meta_oauth_redirect_uri: str = "http://localhost:8000/api/oauth/instagram/callback"
    token_encryption_key: str = ""
    # Local operator secret for connection status / disconnect (not a Meta token).
    app_api_token: str = ""
    database_url: str = "sqlite:///./data/infinityx.db"
    app_base_url: str = "http://localhost:8000"
    frontend_success_url: str = "http://localhost:5173/"
    # Comma-separated browser origins allowed for CORS (never use "*").
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    oauth_scopes: str = DEFAULT_OAUTH_SCOPES
    oauth_state_ttl_seconds: int = 600

    @property
    def meta_configured(self) -> bool:
        return bool(
            self.meta_instagram_app_id.strip()
            and self.meta_instagram_app_secret.strip()
            and self.meta_oauth_redirect_uri.strip()
            and self.token_encryption_key.strip()
        )

    @property
    def scope_list(self) -> list[str]:
        return [s.strip() for s in self.oauth_scopes.split(",") if s.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip().rstrip("/") for o in self.cors_allow_origins.split(",") if o.strip()]
        # Also allow origin derived from frontend success URL when present.
        frontend = self.frontend_success_url.strip().rstrip("/")
        if frontend.startswith("http://") or frontend.startswith("https://"):
            # Keep only scheme://host[:port]
            from urllib.parse import urlsplit

            parts = urlsplit(frontend)
            if parts.scheme and parts.netloc:
                derived = f"{parts.scheme}://{parts.netloc}"
                if derived not in origins:
                    origins.append(derived)
        # Reject accidental wildcards — CORS must be an explicit allowlist.
        return [o for o in origins if o != "*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
