from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.config import get_settings
from app.db import init_db
from app.routes import connection, oauth
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """CORS with an explicit origin allowlist from settings (never '*').

    Credentials are not enabled: the UI authenticates with Authorization /
    X-InfinityX-Token headers, not cookies.
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        allowed = set(settings.cors_origin_list)
        origin = request.headers.get("origin")

        if request.method == "OPTIONS" and origin:
            if origin not in allowed:
                return Response(status_code=403, content="CORS origin not allowed")
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": (
                    "Authorization, Content-Type, Accept, X-InfinityX-Token"
                ),
                "Access-Control-Max-Age": "600",
                "Vary": "Origin",
            }
            return Response(status_code=204, headers=headers)

        response = await call_next(request)
        if origin and origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            # Explicitly do not set Access-Control-Allow-Credentials
        return response


app = FastAPI(
    title="InfinityX",
    description=(
        "Instagram Creator AI agent API. Phase 1: Meta Business Login for Instagram "
        "OAuth and encrypted token storage. Connection status reflects real tokens only."
    ),
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(DynamicCORSMiddleware)

app.include_router(oauth.router)
app.include_router(connection.router)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        meta_configured=settings.meta_configured,
    )
