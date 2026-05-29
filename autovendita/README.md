# AutoVendita 🚗

Marketplace moderno e interattivo per comprare e vendere auto in Italia.

## Funzionalità

- **Homepage** con hero animato, ricerca rapida e auto in evidenza
- **Annunci** con filtri avanzati (marca, carburante, prezzo, anno, cambio)
- **Vendi auto** — form completo per pubblicare annunci gratuiti
- **Dettaglio auto** — modal interattivo con contatto diretto al venditore
- **Design moderno** — dark theme, animazioni Framer Motion, responsive
- **Persistenza locale** — gli annunci creati vengono salvati nel browser

## Avvio rapido

```bash
cd autovendita
npm install
npm run dev
```

Apri [http://localhost:3000](http://localhost:3000)

## Pagine

| Pagina | Percorso | Descrizione |
|--------|----------|-------------|
| Home | `/` | Landing con ricerca e auto in evidenza |
| Annunci | `/annunci` | Catalogo completo con filtri |
| Vendi | `/vendi` | Form per inserire un nuovo annuncio |

## Stack

- Next.js 16 + React 19
- Tailwind CSS 4
- Framer Motion
- Lucide Icons
- TypeScript

## Struttura

```
autovendita/src/
├── app/           # Pagine (App Router)
├── components/    # Componenti UI
├── context/       # State management (CarsContext)
└── lib/           # Tipi, dati, storage
```
