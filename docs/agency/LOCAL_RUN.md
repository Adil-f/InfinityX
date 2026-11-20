# Local run

```bash
npm install
cp apps/agency/.env.example apps/agency/.env.local
python3 packages/scripts/import_leads.py
npm run dev
```

Open http://localhost:3000

Owner secret default: `change-me-local-only`
