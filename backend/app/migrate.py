from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from app.db import engine

MIGRATIONS = (
    ("001_init", "001_init.sql"),
    ("002_access_controls", "002_access_controls.sql"),
)


def _statements(sql: str) -> list[str]:
    lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    parts = []
    for chunk in "\n".join(lines).split(";"):
        statement = chunk.strip()
        if statement:
            parts.append(statement)
    return parts


def _applied() -> set[str]:
    with engine.connect() as conn:
        exists = conn.execute(text("SELECT to_regclass('public.schema_migrations')")).scalar()
        if not exists:
            return set()
        rows = conn.execute(text("SELECT version FROM schema_migrations")).scalars().all()
        return set(rows)


def _apply(filename: str) -> None:
    sql_path = Path(__file__).resolve().parents[1] / "migrations" / filename
    statements = _statements(sql_path.read_text(encoding="utf-8"))
    raw = engine.raw_connection()
    try:
        cursor = raw.cursor()
        for statement in statements:
            cursor.execute(statement)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def migrate() -> None:
    applied = _applied()
    for version, filename in MIGRATIONS:
        if version in applied:
            continue
        _apply(filename)
        applied.add(version)
