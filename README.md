# InfinityX

Personal brand website artifact + **Infinity X AI Agency** (local Phase 2).

> The original website archive `web zip.zip` is preserved and must not be deleted.

## Layout

- `web zip.zip` — original static website (intact)
- `apps/agency` — local Next.js agency app (CRM, builder, approvals)
- `packages/*` — modular libraries (policy, db, orchestrator, agents, builder)
- `templates/*` — compositional website layouts/sections/brand systems
- `packages/scripts` — deterministic Python automation
- `docs/agency` — runbooks

## Agency (local only)

```bash
npm install
cp apps/agency/.env.example apps/agency/.env.local
npm run import:leads
npm run dev
```

Open http://localhost:3000

Default owner secret (change it): see `.env.example`.

### Restrictions (Phase 2)

- No paid APIs, purchases, deployment, publishing
- No external email send / customer outreach
- Forms in generated sites have submission **disabled by default**
- External actions require Approval Dashboard decision

## Tests

```bash
npm run test:all
```

## License

Pending.
