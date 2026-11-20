export function suggestCategory(name: string, fitReason?: string | null): string {
  const t = `${name} ${fitReason || ""}`.toLowerCase();
  if (/ristor|trattor|pizzer|oster|bracer|forno|panific/.test(t)) return "ristorante";
  if (/abbigl|negoz|botteg|shop/.test(t)) return "negozio";
  if (/falegn|artigian|latton|officin/.test(t)) return "artigiano";
  if (/studio|dent|avvoc|consul/.test(t)) return "studio";
  if (/casale|hotel|b&b|ospital|agritur/.test(t)) return "ospitalita";
  return "servizi";
}
