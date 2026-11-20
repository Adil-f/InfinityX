# Phase 2 v2.1 — Verification Report

**Branch:** `cursor/agency-phase2-3253`  
**Date:** 2026-11-20 (Europe/Rome)  
**Status:** Implementation complete — PR for review — **do not merge without approval**

## Constraints honored

| Restriction | Status |
|-------------|--------|
| No paid APIs | OK |
| No purchases | OK |
| No external emails | OK (transport unwired; PolicyBlocked) |
| No customer outreach | OK |
| No production deployment | OK |
| No publishing | OK |
| No destructive GitHub ops | OK |
| `web zip.zip` preserved | OK — SHA256 `0a0d39a10185cad29e95267ab045eadfc3c1543f4bbd01c2fd6af2d2cb0bf611` |

## Test results

| Suite | Result |
|-------|--------|
| `@infinityx/agency` vitest | 1 passed |
| `@infinityx/policy` vitest | 2 passed |
| `@infinityx/website-builder` vitest | 4 passed |
| `@infinityx/orchestrator` vitest | 1 passed |
| `pytest packages/scripts/tests` | 9 passed |
| `next build` | success |
| ZIP integrity `sha256sum -c` | OK |

## Smoke generation

- Lead `Gli Artigiani` → layout `ristorante-editorial`, tests passed, ZIP export created  
- Lead `Cervi Mario & Figlio` → layout `negozio-catalog`, tests passed  
- Draft created for `Il Forno di Orazio` (local only)

## Preview artifacts

- `/opt/cursor/artifacts/preview-ristorante-editorial.png`
- `/opt/cursor/artifacts/preview-negozio-catalog.png`
- HTML copies alongside

## Security findings

1. **Positive:** Email/publish/purchase adapters throw `PolicyBlockedError`; send path audited as `send.blocked_transport` even after approval.  
2. **Positive:** Generated contact forms use `data-submit="disabled"` + disabled button.  
3. **Positive:** SQLite file best-effort mode `0600`; backups with SHA-256.  
4. **Note:** Default `AGENCY_OWNER_SECRET=change-me-local-only` — change before any shared environment.  
5. **Note:** Agency is local-only; no auth hardening for internet exposure (by design Phase 2).  
6. **Note:** npm audit reported transitive vulns in toolchain — not addressed in Phase 2 (no force upgrades).  

## Remaining limitations

- No real Gmail send / hosting deploy (intentional).  
- Website copy is template/deterministic — not LLM-written.  
- Playwright viewport e2e not fully wired (chrome screenshots used for evidence).  
- axe-core/pa11y CLI not installed; a11y checks are structural (SEO/form/alt/layout meta).  
- `data/*` runtime files gitignored (seed committed).  
- AutoVendita / profile repos still not created (out of scope).  

## How to run locally

See `docs/agency/LOCAL_RUN.md`.
