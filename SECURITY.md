# Security

Infinity X is for authorized security work. The controls below are the product boundary, not a suggestion.

## Collection

- Public DNS, RDAP, certificate transparency, RIPEstat, Team Cymru, GitHub, GitLab, Gravatar, and URLhaus are queried as themselves.
- Have I Been Pwned, VirusTotal, AlienVault OTX, Stripe, and the identity provider run only with the operator's credentials. Otherwise the source is unavailable and no result is synthesized.
- The platform does not query NADRA or any private identity registry.
- Phone responses do not include a subscriber name, IMSI, IMEI, or device coordinates. A country and a prefix carrier are numbering-plan metadata. The analyst must supply a country hint or an international `+` prefix. The service does not guess a person from a national number.
- CNIC handling validates format, records consent and an audit event, and stores a redacted value plus a deployment-salted hash. The raw number is not written to findings or to the audit payload.
- Threat lookups send a host or a hash. They do not fetch the URL the analyst pasted, which avoids using the API as a proxy.
- Evidence hashing reads at most 1 MB, returns digests, and drops the bytes.
- Social URL templates are unverified references with confidence 0. Existence is checked only against the public GitHub and GitLab APIs.

## Analysis

The investigator may quote a source that describes infrastructure, including malware-URL listings. Its own prose is filtered against accusation language. Hypotheses are labeled and are not findings. The report states that infrastructure indicators are not a statement about a person's conduct.

Graph edges require a relation from the allow list, an evidence sentence, and a known source. Merging two nodes because they might be the same person is rejected by the API.

## Access

- Passwords are bcrypt hashes and must be at least 12 characters with a letter and a number.
- Access tokens are short-lived HS256 JWTs. MFA tokens cannot call the API. TOTP secrets are encrypted with a key derived from `SECRET_KEY`. MFA stays off until a code verifies.
- Five failed passwords lock the account for 15 minutes.
- Roles limit search, investigation, reporting, billing, source administration, and user administration. API keys intersect those permissions with `search` and `read` only.
- Login and search routes are rate limited in Redis. In `APP_ENV=test` the limit is raised so the suite can run. If Redis is down, the process uses a local window and `/api/v1/health` reports Redis unavailable.
- Production startup refuses a default `SECRET_KEY` and refuses `SEED_DEV_FIXTURES=true`.
- Responses send `X-Frame-Options: DENY`, `nosniff`, `no-referrer`, and a permissions policy that disables geolocation, camera, and microphone.

## Privacy

Every search records a consent row with purpose and lawful basis. CNIC uses the text version `cnic-format-v1`.

`POST /api/v1/gdpr/export` returns the signed-in user's account, consents, API-key prefixes, and investigation titles. It does not include third-party findings. `POST /api/v1/gdpr/delete` anonymizes the user, revokes their keys, and deletes their consent rows. The only remaining owner cannot be deleted until ownership is transferred.

Retention is configurable from 7 to 3650 days. Running it deletes expired case findings and unattached searches older than the policy.

Audit events cover login, search, CNIC checks, graph edits, reports, key management, plan changes, retention, and GDPR actions. Audit details for CNIC do not contain the raw number.

## Stripe

Checkout is a Stripe session when the secret and price are set. This process does not mark an invoice paid by itself. The webhook rejects missing or invalid signatures. A verified `checkout.session.completed` event is the only automatic plan change, and the ledger stores the Stripe event id.

## Deployment notes

The Compose password and fixture admin password are for a local workstation. Replace them, put Postgres and Redis on a private network, and terminate TLS in front of the API and console before anyone else can reach them.
