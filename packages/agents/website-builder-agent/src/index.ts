import fs from "fs";
import path from "path";
import type Database from "better-sqlite3";
import { id, nowIso, writeAudit } from "../../../db/src/client";
import { composeSite } from "../../../website-builder/src/compose";
import { renderSiteFiles, writeSiteToDir } from "../../../website-builder/src/render";
import { exportDirectoryToZip } from "../../../website-builder/src/export";
import { formSubmitDisabled, hasSeoBasics } from "../../../website-builder/src/seo";

export function runWebsiteBuilderAgent(
  db: Database.Database,
  payload: Record<string, unknown>,
  paths: { templatesRoot: string; previewsRoot: string; exportsRoot: string },
) {
  const leadId = String(payload.leadId || "");
  const doExport = Boolean(payload.export);
  const lead = db.prepare(`SELECT * FROM leads WHERE id=?`).get(leadId) as
    | {
        id: string;
        name: string;
        city: string | null;
        region: string | null;
        category: string | null;
        contact_phone: string | null;
        contact_email: string | null;
        fit_reason: string | null;
      }
    | undefined;
  if (!lead) throw new Error("Lead not found");
  const input = {
    id: lead.id,
    name: lead.name,
    city: lead.city,
    region: lead.region,
    category: (payload.category as string) || lead.category,
    contactPhone: lead.contact_phone,
    contactEmail: lead.contact_email,
    fitReason: lead.fit_reason,
  };
  const composition = composeSite(paths.templatesRoot, input);
  const files = renderSiteFiles(input, composition);
  const buildId = id("build");
  const previewId = id("prev");
  const previewDir = path.join(paths.previewsRoot, previewId);
  writeSiteToDir(previewDir, files);

  const tests = {
    seo: hasSeoBasics(files["index.html"]),
    formDisabled: formSubmitDisabled(files["contact.html"] || files["index.html"]),
    layoutMeta: files["index.html"].includes(`data-layout="${composition.layoutFamily}"`),
  };
  const testStatus = Object.values(tests).every(Boolean) ? "passed" : "failed";

  db.prepare(
    `INSERT INTO site_builds (id, lead_id, category, layout_family, brand_system_id, section_graph_json, page_graph_json, created_at)
     VALUES (?,?,?,?,?,?,?,?)`,
  ).run(
    buildId,
    leadId,
    composition.category,
    composition.layoutFamily,
    composition.brandSystemId,
    JSON.stringify(composition.sections),
    JSON.stringify(composition.pages),
    nowIso(),
  );
  db.prepare(
    `INSERT INTO previews (id, build_id, path, last_test_status, created_at) VALUES (?,?,?,?,?)`,
  ).run(previewId, buildId, previewDir, testStatus, nowIso());

  let exportInfo: { exportId: string; zipPath: string; checksum: string } | null = null;
  if (doExport) {
    const exportId = id("exp");
    const exportDir = path.join(paths.exportsRoot, exportId);
    fs.mkdirSync(exportDir, { recursive: true });
    writeSiteToDir(exportDir, files);
    const zipPath = path.join(paths.exportsRoot, `${exportId}.zip`);
    const checksum = exportDirectoryToZip(exportDir, zipPath);
    db.prepare(
      `INSERT INTO export_artifacts (id, build_id, path, checksum, created_at) VALUES (?,?,?,?,?)`,
    ).run(exportId, buildId, zipPath, checksum, nowIso());
    exportInfo = { exportId, zipPath, checksum };
  }

  writeAudit(db, {
    action: "builder.preview",
    resourceType: "preview",
    resourceId: previewId,
    meta: { buildId, layout: composition.layoutFamily, testStatus },
  });

  return {
    buildId,
    previewId,
    previewDir,
    layoutFamily: composition.layoutFamily,
    brandSystemId: composition.brandSystemId,
    structuralSignature: composition.structuralSignature,
    tests,
    testStatus,
    export: exportInfo,
  };
}
