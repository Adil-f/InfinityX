# InfinityX Website

Personal brand website for **Infinity X Developer** (Adil Fayyaz).

## What this is

A static front-end showcase built with HTML, CSS, and JavaScript.

It is:

- a personal developer website
- a UI playground (including the experimental X Store demo)

It is **not**:

- an agency site
- a record of client delivery
- a production e-commerce platform

## Run locally

```bash
cd website
python -m http.server 8000
```

Open http://localhost:8000

Alternative:

```bash
npx serve .
```

## Structure

```text
website/
├── index.html      # Main personal site
├── xstore.html     # Experimental storefront demo
├── styles.css
├── script.js
└── README.md
```

## Notes

- Contact form is front-end only (no backend).
- X Store cart/checkout is simulated.
- External links point to public GitHub repositories.
