# InfinityX

Personal brand website for **Infinity X Developer** — Adil Fayyaz.

> Web Developer building modern digital products and exploring AI-assisted development and cybersecurity research.

## Overview

InfinityX is a static front-end project that presents my personal developer brand.  
It is a portfolio-style website and UI showcase — **not** an agency, company product catalog, or client case-study site.

## Features

- Responsive personal landing page
- About, focus areas, projects, and stack sections aligned with public work
- Experimental **X Store** UI demo (simulated cart only)
- Smooth front-end interactions and animations

## Technology Stack

- HTML5
- CSS3
- JavaScript (vanilla)

## Project structure

```text
InfinityX/
├── README.md
├── docs/                    # Audit notes, plans, publishing guides
├── github-profile/          # Ready-to-publish GitHub Profile README
├── website/                 # Site source (open index.html or serve locally)
│   ├── index.html
│   ├── xstore.html
│   ├── styles.css
│   ├── script.js
│   └── README.md
└── web zip.zip              # Temporary backup of the original archive
```

## Installation / local preview

```bash
cd website
python -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000).

```bash
# alternative
cd website && npx serve .
```

## Related projects

- [AutoVendita](https://github.com/Adil-f/AutoVendita) — car marketplace UI demo/prototype (Next.js)

## Documentation

- [InfinityX restructure plan](docs/INFINITYX_RESTRUCTURE_PLAN.md)
- [Profile publish instructions](docs/PROFILE_PUBLISH_INSTRUCTIONS.md)
- [MIT license proposal](docs/MIT_LICENSE_PROPOSAL.md)
- [Security audit](docs/SECURITY_AUDIT.md)

## Honest positioning

This repository intentionally avoids:

- fake client counts
- fake years of experience
- fake testimonials
- unsupported technology claims

Public claims stay aligned with public repositories.

## License

License pending confirmation. See [MIT proposal](docs/MIT_LICENSE_PROPOSAL.md).
