import fs from "fs";
import path from "path";
import { LAYOUT_FAMILIES } from "../../core/src/index";
import { loadBrand, pickBrandId } from "./brand";
import type { CategoryProfile, LeadInput, SiteComposition } from "./types";

export function loadCategory(templatesRoot: string, category: string): CategoryProfile {
  const p = path.join(templatesRoot, "categories", `${category}.json`);
  if (!fs.existsSync(p)) {
    throw new Error(`Unknown category: ${category}`);
  }
  return JSON.parse(fs.readFileSync(p, "utf8")) as CategoryProfile;
}

export function listBrandIds(templatesRoot: string): string[] {
  const dir = path.join(templatesRoot, "brand-systems");
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""));
}

export function composeSite(
  templatesRoot: string,
  lead: LeadInput,
  categoryOverride?: string,
): SiteComposition {
  const category = (categoryOverride || lead.category || "servizi").toLowerCase();
  const profile = loadCategory(templatesRoot, category);
  if (!LAYOUT_FAMILIES.includes(profile.layoutFamily as (typeof LAYOUT_FAMILIES)[number])) {
    throw new Error(`Invalid layout family: ${profile.layoutFamily}`);
  }
  const brands = listBrandIds(templatesRoot);
  const brandSystemId = pickBrandId(profile.defaultBrand, lead.name, brands);
  const brand = loadBrand(templatesRoot, brandSystemId);

  // Diversity: mutate section order slightly by name hash while keeping contact-form last
  const sections = [...profile.sections];
  const contactIdx = sections.indexOf("contact-form");
  const contact = contactIdx >= 0 ? sections.splice(contactIdx, 1)[0] : null;
  let h = 0;
  for (let i = 0; i < lead.name.length; i++) h += lead.name.charCodeAt(i);
  if (h % 3 === 1 && sections.length > 2) {
    const [a] = sections.splice(1, 1);
    sections.push(a);
  } else if (h % 3 === 2 && sections.length > 3) {
    sections.reverse();
  }
  if (contact) sections.push(contact);

  const structuralSignature = [
    profile.layoutFamily,
    brandSystemId,
    sections.join(">"),
    profile.pages.join("+"),
  ].join("|");

  return {
    leadId: lead.id,
    category: profile.category,
    layoutFamily: profile.layoutFamily,
    brandSystemId,
    brand,
    sections,
    pages: profile.pages,
    nav: profile.nav,
    structuralSignature,
  };
}
