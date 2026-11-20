import path from "path";
import fs from "fs";
import os from "os";
import { describe, expect, it } from "vitest";
import { composeSite } from "./compose";
import { renderSiteFiles, writeSiteToDir } from "./render";
import { isStructurallyDiverse } from "./diversity";
import { formSubmitDisabled, hasSeoBasics } from "./seo";
import { LAYOUT_FAMILIES } from "../../core/src/index";

const root = path.resolve(__dirname, "../../../templates");

describe("website builder", () => {
  it("has 6 layout families", () => {
    expect(LAYOUT_FAMILIES.length).toBeGreaterThanOrEqual(6);
    for (const f of LAYOUT_FAMILIES) {
      expect(fs.existsSync(path.join(root, "layouts", f, "STRUCTURE.md"))).toBe(true);
    }
  });

  it("composes different categories into different layouts", () => {
    const a = composeSite(root, { id: "1", name: "Trattoria Rossi", category: "ristorante", city: "Nardò" });
    const b = composeSite(root, { id: "2", name: "Bottega Blu", category: "negozio", city: "Sassuolo" });
    expect(a.layoutFamily).not.toBe(b.layoutFamily);
    expect(isStructurallyDiverse(a, b)).toBe(true);
  });

  it("renders seo, disabled forms, and layout markers", () => {
    const c = composeSite(root, { id: "3", name: "Studio Verde", category: "studio", city: "Modena" });
    const files = renderSiteFiles({ id: "3", name: "Studio Verde", category: "studio", city: "Modena" }, c);
    expect(hasSeoBasics(files["index.html"])).toBe(true);
    expect(formSubmitDisabled(files["contact.html"] || files["index.html"])).toBe(true);
    expect(files["sitemap.xml"]).toContain("<urlset");
    expect(files["robots.txt"]).toContain("Sitemap");
    expect(files["index.html"]).toContain(`data-layout="${c.layoutFamily}"`);
  });

  it("writes preview directory", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ix-preview-"));
    const c = composeSite(root, { id: "4", name: "Officina Falco", category: "servizi", city: "Bologna" });
    const files = renderSiteFiles({ id: "4", name: "Officina Falco", category: "servizi", city: "Bologna" }, c);
    writeSiteToDir(dir, files);
    expect(fs.existsSync(path.join(dir, "index.html"))).toBe(true);
  });
});
