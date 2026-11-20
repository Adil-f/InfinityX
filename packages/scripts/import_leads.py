#!/usr/bin/env python3
"""Deterministic lead import into SQLite (no AI)."""
from __future__ import annotations
import json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data/seed/leads.seed.json"
DB = ROOT / "data/agency.db"
SCHEMA = (ROOT / "packages/db/src/schema.sql").read_text()

def main() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA)
    leads = json.loads(SEED.read_text(encoding="utf-8"))
    ts = datetime.now(timezone.utc).isoformat()
    for l in leads:
        conn.execute(
            """INSERT INTO leads (id,name,city,region,category,website_status,contact_phone,contact_email,fit_reason,source_url,status,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET name=excluded.name, updated_at=excluded.updated_at""",
            (
                l["id"], l["name"], l.get("city"), l.get("region"), l.get("category"),
                l.get("websiteStatus"), l.get("contactPhone"), l.get("contactEmail"),
                l.get("fitReason"), l.get("sourceUrl"), l.get("status", "new"), ts, ts,
            ),
        )
        conn.execute(
            "INSERT INTO research_notes (id, lead_id, body, source, created_at) VALUES (?,?,?,?,?)",
            (f"rn_{uuid.uuid4()}", l["id"], l.get("fitReason") or "seed", l.get("sourceUrl") or "seed", ts),
        )
    conn.commit()
    print(f"imported {len(leads)} leads into {DB}")

if __name__ == "__main__":
    main()
