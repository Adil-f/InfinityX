import fs from "fs";
import path from "path";
import type { BrandSystem } from "./types";

export function loadBrand(templatesRoot: string, brandId: string): BrandSystem {
  const p = path.join(templatesRoot, "brand-systems", `${brandId}.json`);
  return JSON.parse(fs.readFileSync(p, "utf8")) as BrandSystem;
}

export function pickBrandId(categoryDefault: string, leadName: string, brands: string[]): string {
  let hash = 0;
  for (let i = 0; i < leadName.length; i++) hash = (hash + leadName.charCodeAt(i) * (i + 1)) % 997;
  // Prefer category default, but rotate among brands when hash odd to increase diversity
  if (hash % 2 === 0) return categoryDefault;
  return brands[hash % brands.length] ?? categoryDefault;
}
