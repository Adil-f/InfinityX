# Roadmap

This repository is the foundation: the API, the console, public connectors, and the controls that keep unavailable sources honest. Later work deepens coverage. It should not weaken the boundaries in `SECURITY.md`.

## In this version

- Organization accounts, RBAC, encrypted TOTP enrollment, API keys, audit, consent, retention, and GDPR export/delete.
- Investigations, attributed findings, and an evidence graph that refuses identity merges.
- Universal routing plus Phone, CNIC, Email, Username, Social, IP, Domain, Threat, and local forensic hashing.
- Public DNS, RDAP, crt.sh, Team Cymru, RIPEstat, GitHub, GitLab, Gravatar, and URLhaus.
- Keyed interfaces for HIBP, VirusTotal, OTX, Stripe, and an operator identity provider.
- A local investigator that separates facts, hypotheses, contradictions, timelines, and lawful next sources, and writes Markdown reports.
- Free, Pro, and Enterprise allowances. Stripe Checkout and signed webhooks when configured. Administrative plan changes are labeled as no charge.
- Docker Compose for Postgres, Redis, the API, and the console.
- Pytest coverage for the boundaries above, including live public-source calls that must fail honestly.

## Next

- Queue long certificate-transparency and provider calls on Redis so a slow upstream cannot hold a browser request. The data model already stores search jobs.
- SSO for enterprise organizations, without removing TOTP as a second factor.
- More public or licensed infrastructure sources, each added as a connector with health, attribution, and an unavailable state.
- A licensed breach or malware feed beyond the interfaces already stubbed, still with no fabricated rows.
- Richer report export (PDF) generated from the same Markdown, not from a second narrative.
- Per-connector dashboards for latency and error rate, fed by the health rows that already exist.

## Explicitly out of scope

- Covert device or location tracking, stalkerware, and private subscriber identification.
- Phone-to-person or CNIC-to-person lookups against NADRA or unauthorized people-search databases.
- Scraping behind logins, credential theft, or bypassing provider access controls.
- Placeholder search results that look like a provider responded.
