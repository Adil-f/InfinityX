# InfinityX Architecture — Phase 1 Foundation

**Product:** InfinityX — Instagram Creator AI agent  
**API surface:** Meta **Instagram API with Instagram Login** (host: `graph.instagram.com`)  
**Auth:** Meta **Business Login for Instagram** (OAuth 2.0 authorization code)  
**Phase 1 scope:** Official OAuth connection, encrypted token storage, connection status from real tokens only. No fake engagement, no simulated “connected” dashboards, no publish/message actions without later explicit user confirmation.

---

## 1. Goals and non-goals

### Goals (Phase 1)
- Connect an Instagram **professional** account (Business or Creator / `Media_Creator`) via official Meta OAuth only.
- Persist encrypted Instagram User access tokens in SQLite.
- Expose APIs to **start OAuth** and **report connection status** derived only from stored tokens + optional live profile fetch after a real connection.
- Design for a future Cursor MCP server and agent loop without blocking OAuth.

### Non-goals (this phase)
- Publishing, scheduling, or DMs (require explicit user confirmation in a later phase).
- Invented metrics, mock Instagram dashboards, or “demo connected” state.
- Shipping the MCP server (designed here; implemented later).
- Facebook Page–linked **Instagram API with Facebook Login** (we use Instagram Login so creators do not need a Facebook Page).

---

## 2. High-level services

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌─────────────────────┐
│ Web / UI        │────▶│ FastAPI backend              │────▶│ Meta Instagram API  │
│ (TypeScript)    │     │ - OAuth start / callback     │     │ graph.instagram.com │
│ Connection page │     │ - Connection status          │     │ api.instagram.com   │
└─────────────────┘     │ - Token encrypt/decrypt      │     │ www.instagram.com   │
                        │ - SQLite persistence         │     │   /oauth/authorize  │
┌─────────────────┐     │ - (future) agent tools       │     └─────────────────────┘
│ Cursor MCP      │─ ─ ▶│                              │
│ (later phase)   │     └──────────────────────────────┘
└─────────────────┘              │
                                 ▼
                        ┌──────────────────┐
                        │ SQLite           │
                        │ accounts, tokens │
                        │ oauth_states     │
                        └──────────────────┘
```

| Service | Stack | Responsibility |
| --- | --- | --- |
| **API** | Python FastAPI | OAuth, status, future Graph wrappers, confirmation gates |
| **DB** | SQLite + SQLAlchemy | Accounts, encrypted tokens, CSRF `state`, audit of grants |
| **Crypto** | `cryptography.Fernet` | At-rest encryption of access tokens (key from env) |
| **UI** | TypeScript (minimal) | “Connect Instagram” + status from API; never invent stats |
| **MCP** (later) | TypeScript MCP server | Expose agent tools to Cursor; calls same backend |

---

## 3. Official Meta products and OAuth flow

### Products
- **Instagram Platform** → **Instagram API with Instagram Login**
- Login product name: **Business Login for Instagram**
- App Dashboard path: **Instagram → API setup with Instagram login → Business login settings**
  - Instagram App ID
  - Instagram App Secret
  - OAuth redirect URIs

### OAuth sequence (Phase 1)

1. Client `GET /api/oauth/instagram/start` → backend creates CSRF `state`, stores it, redirects to:
   `https://www.instagram.com/oauth/authorize?client_id=…&redirect_uri=…&response_type=code&scope=…&state=…`
2. User grants permissions in Meta’s authorization window.
3. Meta redirects to `GET /api/oauth/instagram/callback?code=…&state=…` (strip trailing `#_` from `code`).
4. Backend validates `state`, then `POST https://api.instagram.com/oauth/access_token` → short-lived Instagram User access token + `user_id` + granted permissions.
5. Backend `GET https://graph.instagram.com/access_token?grant_type=ig_exchange_token&…` → long-lived token (~60 days).
6. Backend **must** `GET https://graph.instagram.com/me?fields=id,user_id,username,name,account_type`. If `/me` fails, **do not** store or activate the long-lived token.
7. Encrypt token → SQLite only after `/me` succeeds. Connection status becomes `connected` **only** after this succeeds.
8. Later: refresh via `https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&…` before expiry.

**Hard rule:** Until step 7 completes successfully, the API must report `connected: false`. No placeholders. A failed profile fetch leaves no grant.

---

## 4. Required permissions / scopes (Creator accounts)

Creator and Business professional accounts use the same **Instagram API with Instagram Login** permission family (`instagram_business_*`). Request scopes as a comma-separated `scope` query parameter on the authorize URL.

| Scope / permission | Product context | What it enables |
| --- | --- | --- |
| `instagram_business_basic` | Instagram API with Instagram Login | Profile, media list/metadata, baseline account identity (`/me`, media nodes). **Required** for long-lived token refresh. |
| `instagram_business_manage_insights` | User and Media Insights on Instagram API with Instagram Login | Account and media insights (views, reach-style metrics, follower demographics where available). |
| `instagram_business_manage_comments` | Comments APIs | Read/manage comments on the professional account’s media. |
| `instagram_business_content_publish` | Content Publishing | Create media containers and publish (posts/reels/stories as supported). **Phase 1: request only if product needs it; never publish without explicit user confirmation.** |
| `instagram_business_manage_messages` | Messaging / Conversations APIs | Read conversations and send messages. **Phase 1: request only if product needs it; never send without explicit user confirmation.** |

### Phase 1 authorize set (recommended)
For connection + foundation that can later read profile/media/insights without acting:

```
instagram_business_basic,instagram_business_manage_insights,instagram_business_manage_comments
```

Defer adding `instagram_business_content_publish` and `instagram_business_manage_messages` until the confirmation UX for publish/DM exists (or request them early only if App Review planning requires it — still gate all write actions in-app).

### Access levels
- **Standard Access:** accounts you own/manage and have added to the app (dev/test).
- **Advanced Access:** other creators’ accounts → App Review + Business Verification as required by Meta.

Legacy short names (`business_basic`, etc.) were deprecated; use only the `instagram_business_*` names.

---

## 5. Data model (SQLite)

### `instagram_accounts`
| Column | Notes |
| --- | --- |
| `id` | Internal UUID |
| `ig_user_id` | Instagram-scoped user ID from token exchange |
| `username`, `name`, `account_type` | From `/me` after real OAuth (`Business` or `Media_Creator`) |
| `permissions` | Comma-separated granted permissions from Meta |
| `connected_at`, `updated_at` | Timestamps |
| `is_active` | Soft disconnect |

### `oauth_tokens`
| Column | Notes |
| --- | --- |
| `account_id` | FK |
| `access_token_encrypted` | Fernet ciphertext (never store plaintext) |
| `token_type` | e.g. `bearer` |
| `expires_at` | From `expires_in` |
| `obtained_at` | For refresh rules (≥24h before refresh) |

### `oauth_states`
| Column | Notes |
| --- | --- |
| `state` | CSRF nonce |
| `created_at`, `expires_at` | Short TTL |
| `consumed` | One-time use |

No tables for fabricated engagement. Insights tables appear only when real Graph responses are persisted in a later phase.

---

## 6. Encrypted token storage

- Env: `TOKEN_ENCRYPTION_KEY` — Fernet key (`cryptography.fernet.Fernet.generate_key()`).
- Encrypt before INSERT/UPDATE; decrypt only in-process for Graph calls or refresh.
- Never log tokens, codes, or secrets; never return tokens from status APIs.
- Rotate by re-encrypting with a new key offline (documented later); Phase 1 uses a single key.

---

## 7. API surface (Phase 1)

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Public | Liveness |
| `GET` | `/api/oauth/instagram/start` | Public | Create `state`, redirect to Meta authorize URL (or JSON URL if `?format=json`) |
| `GET` | `/api/oauth/instagram/callback` | Public (Meta `state` CSRF) | Exchange code → long-lived token → encrypt → store; redirect to UI status |
| `GET` | `/api/instagram/connection` | **`APP_API_TOKEN`** | `{ connected, account? }` from DB only; no invented stats |
| `DELETE` | `/api/instagram/connection` | **`APP_API_TOKEN`** | Soft-disconnect / clear encrypted tokens |

### Local API token (connection protection)

Phase 1 is local-first: there is no multi-user login yet. Connection **read** and **disconnect** require a shared operator secret `APP_API_TOKEN` via:

- `Authorization: Bearer <APP_API_TOKEN>`, or
- `X-InfinityX-Token: <APP_API_TOKEN>`

This is **not** a Meta Instagram User access token. The UI loads the same value from `VITE_APP_API_TOKEN`. Bearer/header auth (no session cookies) avoids classic cross-site cookie CSRF; CORS does not enable credentials.

### CORS

- Allowlist only: `CORS_ALLOW_ORIGINS` (plus origin derived from `FRONTEND_SUCCESS_URL`).
- Never `allow_origins=["*"]` with credentials; `*` entries are dropped.
- Browser requests with a non-allowlisted `Origin` are rejected with HTTP 403 (preflight and non-preflight).
- `Access-Control-Allow-Credentials` is not set; browsers send the API token in headers when the frontend holds it.

Status payload example when **not** connected:

```json
{ "connected": false }
```

When connected (fields from real OAuth + `/me` only):

```json
{
  "connected": true,
  "account": {
    "ig_user_id": "…",
    "username": "…",
    "name": "…",
    "account_type": "Media_Creator",
    "permissions": ["instagram_business_basic", "…"],
    "connected_at": "…",
    "token_expires_at": "…"
  }
}
```

---

## 8. Agent loop (design; implement later)

```
User intent (Cursor chat / UI)
    → Planner (LLM) proposes tool calls
    → Policy gate: read tools OK if connected;
                   publish / message tools require explicit user confirmation artifact
    → Tool runner → FastAPI → Instagram Graph
    → Observation → LLM → response / next tool
```

- **Read tools** (future): `get_profile`, `list_media`, `get_insights`, `list_comments`.
- **Write tools** (future): `publish_media`, `reply_comment`, `send_message` — blocked until a confirmation record exists for that action.
- Agent never synthesizes follower counts or engagement; if Graph fails or is disconnected, return an explicit error state.

---

## 9. MCP for Cursor (later phase)

- TypeScript MCP server wraps the same FastAPI tools.
- OAuth remains browser/backend; MCP does not own the OAuth redirect.
- Design constraint: shipping OAuth must not wait on MCP. MCP is a client of `/api/*`.

---

## 10. Configuration (env)

| Variable | Purpose |
| --- | --- |
| `META_INSTAGRAM_APP_ID` | Instagram App ID (Business login settings) |
| `META_INSTAGRAM_APP_SECRET` | Instagram App Secret |
| `META_OAUTH_REDIRECT_URI` | Exact redirect URI registered in App Dashboard |
| `TOKEN_ENCRYPTION_KEY` | Fernet key for Instagram tokens at rest |
| `APP_API_TOKEN` | Local operator secret for connection GET/DELETE |
| `CORS_ALLOW_ORIGINS` | Comma-separated browser origins (no `*`) |
| `DATABASE_URL` | SQLite path, e.g. `sqlite:///./data/infinityx.db` |
| `APP_BASE_URL` | Backend public base URL |
| `FRONTEND_SUCCESS_URL` | Where callback redirects after success |
| `OAUTH_SCOPES` | Override default scope list (optional) |
| `VITE_APP_API_TOKEN` | Frontend copy of `APP_API_TOKEN` |

Live OAuth cannot complete until the user supplies App ID, App Secret, and a matching redirect URI in the Meta App Dashboard.

---

## 11. Testing strategy

- Unit/integration tests with **mocked** Meta HTTP (no live network).
- Cover: state creation/consumption, code exchange + long-lived exchange happy path, encryption round-trip, status `connected: false` without tokens, status `connected: true` only after store, CSRF/`state` rejection.
- Fixtures for Meta JSON shapes from Business Login for Instagram docs.

---

## 12. Later feature plug-in map

| Feature | Depends on | Plug-in point |
| --- | --- | --- |
| Media library UI | `instagram_business_basic` + token | `GET` Graph media via service module |
| Insights dashboard | `instagram_business_manage_insights` | Insights service; store raw Graph JSON only |
| Comment triage | `instagram_business_manage_comments` | Comments service + agent read tools |
| Publishing / scheduling | `instagram_business_content_publish` + confirmation | Content publish service + confirmation store |
| Messaging | `instagram_business_manage_messages` + confirmation | Messaging service + webhooks |
| Cursor MCP | Stable `/api` tools | MCP server package |
| Multi-account | Same OAuth | Multiple `instagram_accounts` rows |

---

## 13. Repo layout (Phase 1)

```
backend/          # FastAPI app, crypto, OAuth, SQLite, tests
frontend/         # Minimal TypeScript connection status page
docs/             # (repo) optional mirrors; Project architecture lives in Agent Store
```

Legacy marketing static site (`web zip.zip`) is **not** the product UI and must not present fake Instagram connection state.
