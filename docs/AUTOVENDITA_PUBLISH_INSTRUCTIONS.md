# Publish AutoVendita as a separate repository

Prepared, verified package location (agent environment): `/tmp/AutoVendita-repo`

## Verification already completed

- `npm ci` ✅
- `npm run lint` ✅ (warnings only: `<img>` suggestions)
- `npm run build` ✅
- GitHub Actions workflow added: `.github/workflows/ci.yml` (lint + build)

## Create empty repo (required once)

The cloud token cannot create repositories for your account.

### GitHub UI
1. https://github.com/new
2. Name: `AutoVendita`
3. Public
4. No README / license / gitignore
5. Create

### CLI
```bash
gh repo create Adil-f/AutoVendita --public --description "Italian car marketplace UI demo/prototype — Next.js"
```

## After empty repo exists

Reply: **“Repos Adil-f creati”** and I will push both `Adil-f/Adil-f` and `Adil-f/AutoVendita`.

### Manual push alternative
```bash
cd /tmp/AutoVendita-repo
rm -rf node_modules .next
git init
git add .
git commit -m "Initial commit: AutoVendita demo/prototype with honest docs and CI"
git branch -M main
git remote add origin https://github.com/Adil-f/AutoVendita.git
git push -u origin main
```

## Suggested GitHub metadata

- Description: `Italian car marketplace UI demo/prototype built with Next.js. Demo data + localStorage — not production-ready.`
- Topics: `nextjs` `react` `typescript` `tailwindcss` `marketplace` `demo` `prototype` `frontend`
- Homepage: (after deploy, if any)
