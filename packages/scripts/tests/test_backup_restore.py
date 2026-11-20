from pathlib import Path
import subprocess, hashlib

ROOT = Path(__file__).resolve().parents[3]

def test_backup_and_checksum():
    subprocess.check_call(["python3", str(ROOT / "packages/scripts/import_leads.py")], cwd=ROOT)
    out = subprocess.check_output(["python3", str(ROOT / "packages/scripts/backup_db.py")], cwd=ROOT, text=True)
    lines = [l.strip() for l in out.strip().splitlines() if l.strip()]
    backup = Path(lines[0])
    checksum = lines[1]
    assert backup.exists()
    assert hashlib.sha256(backup.read_bytes()).hexdigest() == checksum
