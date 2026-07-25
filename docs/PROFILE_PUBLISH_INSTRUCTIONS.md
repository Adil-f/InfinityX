# Publish the GitHub Profile README

The Cursor integration token **cannot create new repositories** on your account (`403 Resource not accessible by integration`).  
The Profile README is ready at `github-profile/README.md`. You only need to create the special empty repo once.

## One-time setup (required)

Create the special profile repository with **exactly** this name:

**Repository name:** `Adil-f`  
**Owner:** `Adil-f`  
**Visibility:** Public  
**Initialize with README:** No (empty is best)

### Option A — GitHub UI

1. Open https://github.com/new
2. Repository name: `Adil-f`
3. Public
4. Do **not** add README / .gitignore / license
5. Create repository

### Option B — GitHub CLI (on your machine)

```bash
gh repo create Adil-f/Adil-f --public --description "Infinity X Developer — GitHub profile"
```

## After the empty repo exists

Reply here with: **“Repos Adil-f creati”** (and similarly for AutoVendita if ready).  
I will push the prepared Profile README immediately.

### Manual push (if you prefer)

```bash
mkdir -p /tmp/adil-f-profile && cd /tmp/adil-f-profile
git clone https://github.com/Adil-f/InfinityX.git
cd InfinityX
git checkout cursor/github-profile-professional-2fb4
mkdir -p /tmp/profile-repo
cp github-profile/README.md /tmp/profile-repo/README.md
cd /tmp/profile-repo
git init
git add README.md
git commit -m "Add Infinity X Developer profile README"
git branch -M main
git remote add origin https://github.com/Adil-f/Adil-f.git
git push -u origin main
```

## Profile settings to update manually

GitHub → Settings → Public profile:

| Field | Suggested value |
| --- | --- |
| Name | Adil Fayyaz |
| Bio | Web Developer building modern digital products and exploring AI-assisted development and cybersecurity research. |
| Pronouns | (optional) |
| URL | your portfolio when available |
| Social accounts | only real links |

## Pinning (after repos exist)

Suggested pin order:

1. `Adil-f/Adil-f` (profile)
2. `Adil-f/AutoVendita` (strongest technical demo)
3. `Adil-f/InfinityX` (personal brand site)
