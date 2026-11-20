#!/usr/bin/env python3
from __future__ import annotations
import hashlib, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/agency.db"

def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: restore_db.py <backup.db>")
    src = Path(sys.argv[1])
    sha_file = src.with_suffix(src.suffix + ".sha256") if False else Path(str(src) + "").with_name(src.name.replace(".db", ".sha256"))
    # prefer sibling .sha256 named agency-TS.sha256
    sibling = src.with_suffix(".sha256")
    if not sibling.exists():
        sibling = Path(str(src).replace(".db", ".sha256"))
    raw = src.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if sibling.exists():
        expected = sibling.read_text(encoding="utf-8").strip()
        if digest != expected:
            raise SystemExit("checksum mismatch")
    shutil.copy2(src, DB)
    print(f"restored {src} -> {DB}")

if __name__ == "__main__":
    main()
