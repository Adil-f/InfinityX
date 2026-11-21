from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings, validate_runtime
from app.connectors.catalog import CONNECTORS
from app.db import SessionLocal, ping_database
from app.migrate import migrate
from app.models import ConnectorState
from app.seed import seed
from app.services.ratelimit import get_redis
from app.routers import auth, platform, search


def ensure_connectors() -> None:
    db = SessionLocal()
    try:
        for spec in CONNECTORS:
            if db.get(ConnectorState, spec["id"]) is None:
                db.add(ConnectorState(id=spec["id"], enabled=True))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime(settings)
    migrate()
    ensure_connectors()
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


app.include_router(auth.router)
app.include_router(search.router)
app.include_router(platform.router)


@app.get("/health")
@app.get("/api/v1/health")
def health():
    database = "ok" if ping_database() else "error"
    seeded = False
    if database == "ok":
        from app.models import Organization

        db = SessionLocal()
        try:
            seeded = db.query(Organization).filter(Organization.is_fixture.is_(True)).count() > 0
        except Exception:
            seeded = False
        finally:
            db.close()
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
        "env": settings.app_env,
        "fixtures_seeded": seeded,
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
