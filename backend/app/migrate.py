from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from app.db import engine

MIGRATION_VERSION = "001_init"


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


def migrate() -> None:
    with engine.connect() as conn:
        exists = conn.execute(text("SELECT to_regclass('public.schema_migrations')")).scalar()
        if exists:
            applied = conn.execute(
                text("SELECT 1 FROM schema_migrations WHERE version = :version"),
                {"version": MIGRATION_VERSION},
            ).scalar()
            if applied:
                return
    sql_path = Path(__file__).resolve().parents[1] / "migrations" / "001_init.sql"
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
