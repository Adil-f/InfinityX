import type { SiteComposition } from "./types";

/** Returns true if two compositions are more than a brand/color reskin. */
export function isStructurallyDiverse(a: SiteComposition, b: SiteComposition): boolean {
  if (a.layoutFamily !== b.layoutFamily) return true;
  if (a.sections.join(">") !== b.sections.join(">")) return true;
  if (a.pages.join("+") !== b.pages.join("+")) return true;
  // Same layout+sections: different brand alone is NOT enough
  return false;
}

export function assertDiverseOrDifferentCategory(
  a: SiteComposition,
  b: SiteComposition,
): void {
  if (a.category !== b.category) return;
  if (!isStructurallyDiverse(a, b) && a.brandSystemId === b.brandSystemId) {
    throw new Error(
      "Diversity failure: compositions differ only by trivial fields (or not at all).",
    );
  }
}
