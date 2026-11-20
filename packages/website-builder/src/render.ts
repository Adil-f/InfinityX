import fs from "fs";
import path from "path";
import type { LeadInput, SiteComposition } from "./types";

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function cssVars(c: SiteComposition): string {
  const b = c.brand;
  return `:root{
  --bg:${b.colors.bg};--ink:${b.colors.ink};--primary:${b.colors.primary};
  --accent:${b.colors.accent};--muted:${b.colors.muted};--radius:${b.radius};
  --display:${b.displayFont};--body:${b.bodyFont};
}`;
}

function baseCss(layout: string): string {
  const common = `
*{box-sizing:border-box}body{margin:0;font-family:var(--body);background:var(--bg);color:var(--ink);line-height:1.5}
img{max-width:100%;height:auto}a{color:var(--primary)}
.wrap{width:min(1100px,92%);margin:0 auto}
.btn{display:inline-block;padding:.75rem 1.1rem;background:var(--primary);color:#fff;text-decoration:none;border-radius:var(--radius);border:0}
.muted{color:var(--muted)}
.section{padding:3rem 0}
h1,h2,h3{font-family:var(--display);line-height:1.15}
nav a{margin-right:1rem;text-decoration:none;color:var(--ink)}
form[data-submit="disabled"] button{opacity:.6;cursor:not-allowed}
.notice{font-size:.9rem;color:var(--muted);margin-top:.5rem}
@media (max-width:900px){.desktop-only{display:none}}
@media (min-width:901px){.mobile-only{display:none}}
@media (max-width:700px){.stack-mobile{flex-direction:column!important}}
`;
  const layouts: Record<string, string> = {
    "ristorante-editorial": `
.layout-ristorante{display:grid;grid-template-columns:240px 1fr;min-height:100vh}
.side{position:sticky;top:0;height:100vh;padding:2rem 1.25rem;border-right:1px solid color-mix(in srgb,var(--ink) 12%,transparent);background:color-mix(in srgb,var(--bg) 90%,var(--accent))}
.hero-ed{padding:4rem 2rem;display:grid;gap:1rem}
.menu-board{columns:2;column-gap:2rem}
.menu-board h3{break-after:avoid}
@media (max-width:800px){.layout-ristorante{grid-template-columns:1fr}.side{position:relative;height:auto;border-right:0;border-bottom:1px solid color-mix(in srgb,var(--ink) 12%,transparent)}.menu-board{columns:1}}
`,
    "negozio-catalog": `
.util{display:flex;justify-content:space-between;align-items:center;padding:.75rem 0;border-bottom:1px solid color-mix(in srgb,var(--ink) 10%,transparent);font-size:.9rem}
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0}
.chip{border:1px solid var(--muted);padding:.35rem .7rem;border-radius:999px}
.grid-cat{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
.card{border:1px solid color-mix(in srgb,var(--ink) 12%,transparent);border-radius:var(--radius);padding:1rem;background:#fff}
@media (max-width:900px){.grid-cat{grid-template-columns:repeat(2,1fr)}}
@media (max-width:600px){.grid-cat{grid-template-columns:1fr}}
`,
    "artigiano-workshop": `
.split{display:flex;gap:0;min-height:70vh}
.split > div{flex:1;padding:3rem 2rem}
.split-visual{background:linear-gradient(135deg,var(--primary),var(--accent));color:#fff}
.timeline{max-width:640px;margin:0 auto;border-left:3px solid var(--primary);padding-left:1.5rem}
.timeline .step{margin:0 0 2rem}
@media (max-width:800px){.split{flex-direction:column}}
`,
    "studio-professional": `
.studio{max-width:820px;margin:0 auto;padding:2rem 1rem}
.topnav{display:flex;justify-content:center;gap:1.5rem;padding:1.25rem 0;border-bottom:1px solid color-mix(in srgb,var(--ink) 10%,transparent)}
.hero-c{text-align:center;padding:4rem 1rem}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
.cards article{padding:1.25rem;border:1px solid color-mix(in srgb,var(--ink) 12%,transparent);border-radius:var(--radius)}
@media (max-width:800px){.cards{grid-template-columns:1fr}}
`,
    "servizi-local": `
.local{display:grid;grid-template-columns:320px 1fr;min-height:100vh}
.rail{background:var(--ink);color:var(--bg);padding:2rem 1.25rem}
.rail a{color:var(--primary)}
.map{min-height:360px;background:repeating-linear-gradient(45deg,color-mix(in srgb,var(--muted) 25%,transparent),color-mix(in srgb,var(--muted) 25%,transparent) 10px,transparent 10px,transparent 20px);display:grid;place-items:center;border:1px dashed var(--muted)}
.svc li{padding:.75rem 0;border-bottom:1px solid color-mix(in srgb,var(--ink) 12%,transparent)}
@media (max-width:850px){.local{grid-template-columns:1fr}}
`,
    "hospitality-welcome": `
.bleed{min-height:85vh;display:grid;align-items:end;padding:3rem;background:radial-gradient(circle at 20% 20%,var(--accent),var(--primary) 45%,var(--ink));color:#fff}
.bands .band{padding:2.5rem 0;border-bottom:1px solid color-mix(in srgb,var(--ink) 10%,transparent)}
.band-inner{display:flex;gap:2rem;align-items:center}
@media (max-width:800px){.band-inner{flex-direction:column;align-items:flex-start}}
`,
  };
  return common + (layouts[layout] || "");
}

function contactForm(lead: LeadInput): string {
  return `
<section class="section" id="contatti">
  <div class="wrap">
    <h2>Contatti</h2>
    <p class="muted">${esc(lead.city || "")}${lead.region ? ", " + esc(lead.region) : ""}</p>
    ${lead.contactPhone ? `<p>Tel: ${esc(lead.contactPhone)}</p>` : ""}
    ${lead.contactEmail ? `<p>Email: ${esc(lead.contactEmail)}</p>` : ""}
    <form data-submit="disabled" action="#" method="post" onsubmit="return false;">
      <label>Nome<br/><input name="name" required /></label><br/><br/>
      <label>Messaggio<br/><textarea name="message" rows="4" required></textarea></label><br/><br/>
      <button type="submit" disabled aria-disabled="true">Invia (disabilitato in preview)</button>
      <p class="notice">Invio form disabilitato per sicurezza. Abilitazione richiede approvazione umana.</p>
    </form>
  </div>
</section>`;
}

function sectionHtml(id: string, lead: LeadInput, c: SiteComposition): string {
  const name = esc(lead.name);
  const city = esc(lead.city || "Italia");
  switch (id) {
    case "hero-editorial":
      return `<section class="hero-ed"><p class="muted">Cucina locale · ${city}</p><h1>${name}</h1><p>${esc(lead.fitReason || "Sapori autentici e accoglienza.")}</p><a class="btn" href="menu.html">Vedi il menu</a></section>`;
    case "hero-shop":
      return `<section class="section"><div class="wrap"><h1>${name}</h1><p class="muted">Negozio a ${city}</p><div class="chips"><span class="chip">Novità</span><span class="chip">Locali</span><span class="chip">Su misura</span></div></div></section>`;
    case "hero-split":
      return `<section class="split"><div class="split-visual"><h1>${name}</h1><p>Laboratorio artigiano</p></div><div><h2>Fatto a mano</h2><p>${esc(lead.fitReason || "Lavorazioni su commissione.")}</p></div></section>`;
    case "hero-centered":
      return `<section class="hero-c"><h1>${name}</h1><p class="muted">Studio professionale · ${city}</p><a class="btn" href="services.html">I nostri servizi</a></section>`;
    case "hero-rail":
      return `<section class="section"><div class="wrap"><h1>${name}</h1><p>Servizi locali a ${city}</p></div></section>`;
    case "hero-bleed":
      return `<section class="bleed"><div><p class="muted">Benvenuti</p><h1>${name}</h1><p>${city}</p></div></section>`;
    case "menu-board":
      return `<section class="section"><div class="wrap"><h2>Menu</h2><div class="menu-board"><div><h3>Antipasti</h3><p>Selezione dello chef</p></div><div><h3>Primi</h3><p>Pasta e zuppe</p></div><div><h3>Secondi</h3><p>Carne e pesce</p></div><div><h3>Dolci</h3><p>Fatti in casa</p></div></div></div></section>`;
    case "catalog-grid":
      return `<section class="section"><div class="wrap"><h2>In evidenza</h2><div class="grid-cat"><article class="card"><h3>Prodotto 1</h3><p class="muted">Disponibile</p></article><article class="card"><h3>Prodotto 2</h3><p class="muted">Disponibile</p></article><article class="card"><h3>Prodotto 3</h3><p class="muted">Disponibile</p></article></div></div></section>`;
    case "process-steps":
      return `<section class="section"><div class="timeline"><div class="step"><h3>01 · Ascolto</h3><p>Capiamo il progetto</p></div><div class="step"><h3>02 · Creazione</h3><p>Lavorazione artigianale</p></div><div class="step"><h3>03 · Consegna</h3><p>Finitura e ritiro</p></div></div></section>`;
    case "services-cards":
      return `<section class="section"><div class="wrap cards"><article><h3>Consulenza</h3><p>Analisi esigenze</p></article><article><h3>Progetto</h3><p>Piano operativo</p></article><article><h3>Follow-up</h3><p>Supporto continuo</p></article></div></section>`;
    case "services-list":
      return `<section class="section"><div class="wrap"><ul class="svc"><li>Intervento rapido</li><li>Preventivo trasparente</li><li>Zona ${city}</li></ul></div></section>`;
    case "welcome-stack":
      return `<section class="bands"><div class="band"><div class="wrap band-inner"><div><h2>Il soggiorno</h2><p>Comfort e cortesia</p></div><div class="muted">Check-in flessibile</div></div></div></section>`;
    case "about-story":
      return `<section class="section"><div class="wrap"><h2>Chi siamo</h2><p>${esc(lead.fitReason || name + " serve la comunità locale con cura.")}</p></div></section>`;
    case "gallery-strip":
    case "gallery-masonry":
      return `<section class="section"><div class="wrap"><h2>Gallery</h2><p><img alt="Atmosfera di ${name}" width="800" height="280" src="data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='800' height='280'><rect fill='%23ddd' width='100%' height='100%'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='%2666' font-family='sans-serif'>${name}</text></svg>`)}" /></p></div></section>`;
    case "faq-list":
      return `<section class="section"><div class="wrap"><h2>FAQ</h2><details><summary>Come contattarci?</summary><p>Usa il form (invio disabilitato in preview) o il telefono.</p></details></div></section>`;
    case "map-block":
      return `<section class="section"><div class="wrap"><h2>Dove siamo</h2><div class="map" role="img" aria-label="Mappa schematica ${city}">${city}</div></div></section>`;
    case "cta-band":
      return `<section class="section" style="background:color-mix(in srgb,var(--primary) 12%,var(--bg))"><div class="wrap"><h2>Parliamone</h2><a class="btn" href="contact.html">Contatti</a></div></section>`;
    case "contact-form":
      return contactForm(lead);
    default:
      return `<section class="section"><div class="wrap"><h2>${esc(id)}</h2></div></section>`;
  }
}

function shell(layout: string, lead: LeadInput, c: SiteComposition, bodyInner: string, title: string, description: string, pagePath: string): string {
  const nav = c.nav.map((n) => `<a href="${esc(n.href)}">${esc(n.label)}</a>`).join("");
  let body = "";
  if (layout === "ristorante-editorial") {
    body = `<div class="layout-ristorante"><aside class="side"><strong>${esc(lead.name)}</strong><nav>${nav}</nav></aside><main>${bodyInner}</main></div>`;
  } else if (layout === "negozio-catalog") {
    body = `<div class="wrap util"><span>${esc(lead.city || "")}</span><nav>${nav}</nav></div>${bodyInner}`;
  } else if (layout === "artigiano-workshop") {
    body = `<header class="wrap" style="padding:1rem 0"><nav>${nav}</nav></header>${bodyInner}`;
  } else if (layout === "studio-professional") {
    body = `<div class="studio"><nav class="topnav">${nav}</nav>${bodyInner}</div>`;
  } else if (layout === "servizi-local") {
    body = `<div class="local"><aside class="rail"><strong>${esc(lead.name)}</strong><nav>${nav}</nav><ul class="svc"><li>Preventivi</li><li>Urgenze</li></ul></aside><main>${bodyInner}</main></div>`;
  } else {
    body = `<header class="wrap" style="padding:1rem 0;display:flex;justify-content:space-between"><strong>${esc(lead.name)}</strong><nav>${nav}</nav></header>${bodyInner}`;
  }

  return `<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}" />
<link rel="canonical" href="/${esc(pagePath)}" />
<meta property="og:title" content="${esc(title)}" />
<meta property="og:description" content="${esc(description)}" />
<meta name="generator" content="InfinityX Website Builder" />
<meta name="ix-layout" content="${esc(layout)}" />
<meta name="ix-brand" content="${esc(c.brandSystemId)}" />
<meta name="ix-signature" content="${esc(c.structuralSignature)}" />
<style>${cssVars(c)}
${baseCss(layout)}</style>
</head>
<body data-layout="${esc(layout)}" data-brand="${esc(c.brandSystemId)}">
${body}
<script>
document.querySelectorAll('form[data-submit="disabled"]').forEach((f)=>{
  f.addEventListener('submit', (e)=>{ e.preventDefault(); alert('Invio disabilitato in preview.'); });
});
</script>
</body></html>`;
}

export function renderSiteFiles(lead: LeadInput, c: SiteComposition): Record<string, string> {
  const files: Record<string, string> = {};
  const desc = `${lead.name} a ${lead.city || "Italia"} — sito generato localmente da Infinity X.`;
  const homeSections = c.sections.map((s) => sectionHtml(s, lead, c)).join("\\n");
  files["index.html"] = shell(c.layoutFamily, lead, c, homeSections, `${lead.name} | Home`, desc, "index.html");

  // Extra pages with subset of sections for IA diversity
  for (const page of c.pages) {
    if (page === "home") continue;
    const file =
      page === "menu" ? "menu.html" :
      page === "catalog" ? "catalog.html" :
      page === "process" ? "process.html" :
      page === "services" ? "services.html" :
      page === "stay" ? "stay.html" :
      page === "contact" ? "contact.html" : `${page}.html`;
    let inner = "";
    if (page === "contact") inner = contactForm(lead);
    else if (page === "menu") inner = sectionHtml("menu-board", lead, c);
    else if (page === "catalog") inner = sectionHtml("catalog-grid", lead, c);
    else if (page === "process") inner = sectionHtml("process-steps", lead, c);
    else if (page === "services") inner = sectionHtml("services-cards", lead, c) + sectionHtml("services-list", lead, c);
    else if (page === "stay") inner = sectionHtml("welcome-stack", lead, c);
    else inner = sectionHtml("about-story", lead, c);
    files[file] = shell(c.layoutFamily, lead, c, inner, `${lead.name} | ${page}`, desc, file);
  }

  files["styles.css"] = `/* Tokens mirrored in page <style>; kept for export clarity */\\n${cssVars(c)}\\n`;
  files["robots.txt"] = `User-agent: *\\nAllow: /\\nSitemap: /sitemap.xml\\n`;
  const urls = Object.keys(files).filter((f) => f.endsWith(".html"));
  files["sitemap.xml"] = `<?xml version="1.0" encoding="UTF-8"?>\\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n` +
    urls.map((u) => `  <url><loc>/${u}</loc></url>`).join("\\n") +
    `\\n</urlset>\\n`;
  return files;
}

export function writeSiteToDir(outDir: string, files: Record<string, string>): void {
  fs.mkdirSync(outDir, { recursive: true });
  for (const [name, content] of Object.entries(files)) {
    fs.writeFileSync(path.join(outDir, name), content, "utf8");
  }
}
