# Infinity X Global OSINT

Authorized intelligence workspace for cybersecurity teams, digital forensics, and investigations that are allowed to use public sources and licensed providers. The product collects, normalizes, correlates, and reports. It does not invent results.

The original InfinityX marketing site is preserved, unchanged in purpose, under `legacy/marketing/`. The archive `web zip.zip` is still in the repository root.

## Run with Docker

Docker Compose starts PostgreSQL 16, Redis 7, the FastAPI service, and the Next.js console.

```bash
docker compose up --build
```

- Console: http://localhost:3000
- API: http://localhost:8000/api/v1/health
- OpenAPI: http://localhost:8000/docs

The compose file is a local development stack. It seeds one fixture organization and sets `APP_ENV=development`. Change `SECRET_KEY` and `ADMIN_PASSWORD`, and set `SEED_DEV_FIXTURES=false`, before any shared deployment. `APP_ENV=production` refuses the default secret and refuses to seed fixtures.

Copy `.env.example` to `.env` when you run the API outside Compose and need optional provider keys. Compose already injects the local database URL, so a laptop `.env` pointing at `127.0.0.1` does not override the Compose network settings.

## Run without Docker

PostgreSQL and Redis must be reachable.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export APP_ENV=development SEED_DEV_FIXTURES=true
export DATABASE_URL=postgresql+psycopg://infinityx:infinityx@127.0.0.1:5432/infinityx
export REDIS_URL=redis://127.0.0.1:6379/0
export SECRET_KEY=dev-only-change-me-not-for-production
cd backend && uvicorn app.main:app --reload --port 8000
```

In another shell:

```bash
cd frontend
npm install
npm run dev
```

The API applies the SQL files in `backend/migrations/` on startup.

Local fixture login, only when seeding is enabled:

- Email: `admin@infinityx.local`
- Password: `ChangeMe-Local-Only-1`

That account is marked as a development fixture. Searches it runs are not fixture intelligence.

## What is real

These connectors call public services when the network allows it. A timeout or HTTP error is stored as an error. An empty answer is described as an empty answer, not as a clean bill of health.

| Source | What it returns |
| --- | --- |
| DNS | A, AAAA, NS, MX, SOA, TXT, SPF, DMARC, common DKIM selectors, PTR |
| RDAP | Public registration status, nameservers, events, registrar via rdap.org |
| crt.sh | Certificate transparency names |
| Team Cymru | IP-to-ASN over DNS. The country is network registration, not a device location |
| RIPEstat | Prefix overview and ASN holder |
| GitHub and GitLab | Public profile by username |
| Gravatar | Whether a public avatar exists for the email hash |
| URLhaus | Public malware-URL listings for a host. The submitted URL is not fetched |
| libphonenumber | Offline numbering-plan format, country, number type, prefix carrier |
| Local hashing | SHA-256, SHA-1, and MD5 of analyst-supplied bytes. Content is not stored |

## What stays unavailable until configured

No sample payload is substituted.

| Variable | Connector |
| --- | --- |
| `HIBP_API_KEY` | Have I Been Pwned |
| `VIRUSTOTAL_API_KEY` | VirusTotal |
| `OTX_API_KEY` | AlienVault OTX |
| `GITHUB_TOKEN` | Optional. Public GitHub works without it |
| `STRIPE_SECRET_KEY`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_ENTERPRISE` | Stripe Checkout. Nothing is charged locally |
| `STRIPE_WEBHOOK_SECRET` | Signed Stripe webhooks |
| `AUTHORIZED_IDENTITY_PROVIDER_URL`, `AUTHORIZED_IDENTITY_PROVIDER_TOKEN` | Not used by CNIC search. Setting them does not send a CNIC to a provider. NADRA is not queried |

Other settings: `APP_ENV`, `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `PUBLIC_APP_URL`, `SEED_DEV_FIXTURES`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME`, `ACCESS_TOKEN_MINUTES`.

## What is a fixture

- The seeded organization Infinity X Labs, its owner, and the team named Core investigations, when `SEED_DEV_FIXTURES=true`.
- The preserved marketing brochure, including its illustrative project counts. Those numbers are not OSINT metrics.
- Unit-test DNS and RDAP payloads. They exercise parsers and are not served by the API.

Search responses set `is_fixture` to false. A result marked as a fixture is dropped before it is returned or stored.

## Tests

```bash
cd backend && pytest -q
```

The suite covers classification, phone and CNIC boundaries, graph policy, the local analyst, connector parsers, auth, RBAC, credits, MFA, GDPR export, and live public-source honesty. Live checks accept a real error. They do not accept a fabricated success.

## Console

Overview, Universal Search, Phone, CNIC, Email, Username, Social, IP, Domain, Threat, Digital Forensics, AI Investigator, Reports, Source Management, API Management, Billing, and Administration. Light and dark themes are available from the top bar.
