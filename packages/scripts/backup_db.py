#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/agency.db"
BACKUPS = ROOT / "data/backups"


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"missing db: {DB}")
    BACKUPS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = BACKUPS / f"agency-{ts}.db"
    shutil.copy2(DB, dest)
    checksum = hashlib.sha256(dest.read_bytes()).hexdigest()
    meta = BACKUPS / f"agency-{ts}.sha256"
    meta.write_text(checksum + "\n", encoding="utf-8")
    try:
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO backup_runs (id, path, checksum, created_at) VALUES (?,?,?,?)",
            (
                f"bak_{uuid.uuid4()}",
                str(dest),
                checksum,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    except Exception as e:
        print("warning: could not write backup_runs:", e)
    print(dest)
    print(checksum)


if __name__ == "__main__":
    main()
