from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings, validate_runtime
from app.db import SessionLocal, ping_database
from app.migrate import migrate
from app.seed import seed
from app.services.ratelimit import get_redis
from app.routers import auth, platform, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime(settings)
    migrate()
    if settings.seed_dev_fixtures and settings.app_env != "test":
        seed()
    yield


app = FastAPI(
    title="Infinity X Global OSINT",
    version="0.1.0",
    summary="Authorized public-source intelligence for security teams.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


MAX_REQUEST_BYTES = 2_000_000


class RequestSizeLimit:
    def __init__(self, app, max_bytes: int = MAX_REQUEST_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        chunks = []
        total = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                chunks.append(message)
                continue
            total += len(message.get("body") or b"")
            chunks.append(message)
            if total > self.max_bytes:
                body = b'{"detail":"Request body is too large"}'
                await send({"type": "http.response.start", "status": 413, "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ]})
                await send({"type": "http.response.body", "body": body})
                return
            if not message.get("more_body", False):
                break
        index = 0

        async def replay():
            nonlocal index
            message = chunks[index]
            index += 1
            return message

        await self.app(scope, replay, send)


app.add_middleware(RequestSizeLimit)
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(platform.router)


@app.get("/health")
@app.get("/api/v1/health")
def health():
    database = "ok" if ping_database() else "error"
    redis_client = get_redis()
    redis_status = "unavailable"
    if redis_client is not None:
        try:
            redis_client.ping()
            redis_status = "ok"
        except Exception:
            redis_status = "unavailable"
    body = {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "redis": redis_status,
        "boundaries": "Public sources and configured authorized providers only. No covert surveillance.",
    }
    status = 200 if database == "ok" else 503
    return JSONResponse(status_code=status, content=body)


@app.get("/api/v1")
def root():
    return {
        "name": "Infinity X Global OSINT",
        "version": "0.1.0",
        "boundaries": "Public sources and authorized providers only. No covert surveillance.",
    }
