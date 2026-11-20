from pathlib import Path
import json, subprocess, sqlite3, os, tempfile, shutil

ROOT = Path(__file__).resolve().parents[3]

def test_seed_has_multiple_categories():
    leads = json.loads((ROOT / "data/seed/leads.seed.json").read_text(encoding="utf-8"))
    cats = {l["category"] for l in leads}
    assert len(cats) >= 5

def test_import_script(tmp_path, monkeypatch):
    # run against real seed into temp copy via env by patching paths is heavy; just ensure script runs on repo db copy
    db = ROOT / "data/agency.db"
    if db.exists():
        db.unlink()
    subprocess.check_call(["python3", str(ROOT / "packages/scripts/import_leads.py")], cwd=ROOT)
    conn = sqlite3.connect(db)
    n = conn.execute("select count(*) from leads").fetchone()[0]
    assert n >= 6
