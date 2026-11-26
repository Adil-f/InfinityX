# InfinityX

Instagram Creator AI agent. **Phase 1** connects a professional Instagram account through official Meta **Business Login for Instagram**, stores encrypted tokens in SQLite, and reports connection status from real tokens only.

There is no simulated Instagram dashboard and no invented engagement metrics.

## Stack

- **Backend:** Python FastAPI, SQLAlchemy, SQLite, Fernet token encryption, httpx
- **Frontend:** TypeScript + Vite (connection status UI)
- **API:** Meta **Instagram API with Instagram Login** (`graph.instagram.com`)

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with Meta credentials + TOKEN_ENCRYPTION_KEY
uvicorn app.main:app --reload --port 8000
```

Generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and use **Connect with Instagram**.

### 3. Meta App Dashboard

1. Create a Meta app and add the **Instagram** product with **API setup with Instagram login**.
2. Under **Business login settings**, copy **Instagram App ID** and **Instagram App Secret**.
3. Add OAuth redirect URI exactly matching `META_OAUTH_REDIRECT_URI` (default: `http://localhost:8000/api/oauth/instagram/callback`).
4. Put values in `backend/.env`.

Live OAuth cannot complete until App ID, App Secret, and redirect URI are set.

## Phase 1 scopes

Default authorize scopes:

- `instagram_business_basic`
- `instagram_business_manage_insights`
- `instagram_business_manage_comments`

Publishing (`instagram_business_content_publish`) and messaging (`instagram_business_manage_messages`) are designed for later phases with explicit user confirmation.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Liveness + whether Meta env is configured |
| `GET /api/oauth/instagram/start` | Begin OAuth (redirect or `?format=json`) |
| `GET /api/oauth/instagram/callback` | OAuth callback → encrypt & store tokens |
| `GET /api/instagram/connection` | `{ connected }` from real tokens only |
| `DELETE /api/instagram/connection` | Clear stored connection |

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Tests mock Meta HTTP and never call live Instagram APIs.

## Architecture

Project architecture (services, data model, OAuth, agent/MCP plug-ins) lives in the Cursor Project store at `docs/architecture.md`.
