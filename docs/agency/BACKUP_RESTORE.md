# Backup / restore

```bash
python3 packages/scripts/backup_db.py
python3 packages/scripts/restore_db.py data/backups/agency-TIMESTAMP.db
```

DB file mode best-effort `0600`. Checksums stored as `.sha256` siblings.
