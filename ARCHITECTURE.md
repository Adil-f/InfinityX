# Architecture

Infinity X is one API and one web console. PostgreSQL is the system of record. Redis is the rate-limit and health-cache store, with a process-local fallback that the health endpoint reports as unavailable rather than pretending Redis is up.

```
browser  ->  Next.js console  ->  FastAPI  ->  PostgreSQL
                                  |-> Redis (rate limit)
                                  |-> public DNS, RDAP, crt.sh, RIPEstat, URLhaus, GitHub, GitLab
                                  |-> keyed providers only when configured
```

Go, Rust, Java, and C++ are not in this repository. DNS and RDAP fan-out uses a Python thread pool with explicit timeouts, which is enough for one analyst request at a time. Evidence hashing is SHA-256, SHA-1, and MD5 over at most 1 MB in the API process. A separate binary would duplicate attribution, audit, and timeout handling without a measured bottleneck.

## Backend

`backend/app/main.py` exposes `/api/v1`. Authentication is a bearer JWT. API keys are hashed, scoped to `search` and `read`, and cannot administer the organization. Roles are owner, admin, investigator, analyst, viewer, and billing.

Search flow:

1. Classify the query, or accept an explicit module. A bare 13-digit number stays ambiguous.
2. Refuse the search when an external module would run and the organization has no credits. The refusal happens before any network call.
3. Call only enabled connectors. Missing keys return `unavailable` and no findings.
4. Normalize, dedupe on source plus entity plus title, and attach attribution, timestamp, and confidence.
5. Persist the job. CNIC values are redacted before they are written. File bytes are hashed and discarded.
6. Project explicit evidence links into the investigation graph. Identity relations are rejected.

The graph allows infrastructure and public-account relations such as `has_mx`, `resolves_to`, `has_asn`, and `public_account`. It rejects `same_person`, subscriber, device, and location relations. Analyst-authored links use the source `analyst_record`, are capped at confidence 0.4, and are labeled in the API.

The investigator is a deterministic pass over stored findings. Facts, references, hypotheses, contradictions, a timeline, and lawful next sources are separate fields. The disclaimer is fixed: the analysis does not accuse a person of a crime. No external model is called.

Billing stores plan allowances and a credit ledger. Stripe Checkout is created only when the secret and price id exist. The webhook updates a plan only after Stripe's signature check. An administrator can set a plan; the ledger reason says no charge was made.

## Data

`backend/migrations/001_init.sql` creates organizations, users, teams, API keys, audit, consent, investigations, search jobs, findings, graph nodes and edges, reports, connector state, and the credit ledger. Findings cannot be stored with `is_fixture = true`.

Retention is per organization. The admin run marks investigations past `retention_until` as expired and deletes their findings, and it deletes old search jobs that were never attached to a case.

## Console

The Next.js App Router console is a client of the API. Theme, session token, and the selected investigation live in the browser. Every module page submits to `/api/v1/search` or `/api/v1/forensics`. Source health, API keys, billing, administration, reports, and the graph call the matching API routes. There is no second cache of search results in the browser beyond the last response.

## Boundaries in the design

Phone metadata comes from libphonenumber's offline numbering plan. CNIC logic checks the published 13-digit shape and series prefix, then offers the authorized-provider interface. That interface sends an identifier only to an operator-configured HTTPS URL. The provider payload is returned to the analyst and is not written into findings. People-search databases, login-gated scraping, and device location are not connectors.
