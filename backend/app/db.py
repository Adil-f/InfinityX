from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def _ensure_sqlite_parent(database_url: str) -> None:
    if database_url.startswith("sqlite:///"):
        path = database_url.removeprefix("sqlite:///")
        if path in {":memory:", ""}:
            return
        if not path.startswith("/"):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        else:
            Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_engine(database_url: str | None = None):
    global _engine, _SessionLocal
    if _engine is not None and database_url is None:
        return _engine
    url = database_url or get_settings().database_url
    _ensure_sqlite_parent(url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine_kwargs: dict = {"connect_args": connect_args, "future": True}
    # Share a single in-memory SQLite across connections (needed for tests + FastAPI).
    if url.startswith("sqlite") and ":memory:" in url:
        engine_kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **engine_kwargs)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _engine = engine
    _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine


def init_db(database_url: str | None = None) -> None:
    engine = get_engine(database_url)
    # Import models so metadata is populated
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    """Test helper: drop global engine so a new DB URL can be used."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
