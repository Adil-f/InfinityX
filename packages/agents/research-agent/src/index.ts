import fs from "fs";
import type Database from "better-sqlite3";
import { id, nowIso, writeAudit } from "../../../db/src/client";

export function runResearchAgent(db: Database.Database, payload: Record<string, unknown>) {
  const seedPath = String(payload.seedPath || "");
  if (!seedPath || !fs.existsSync(seedPath)) throw new Error("seedPath required");
  const leads = JSON.parse(fs.readFileSync(seedPath, "utf8")) as Array<Record<string, unknown>>;
  const upsert = db.prepare(`INSERT INTO leads (
    id,name,city,region,category,website_status,contact_phone,contact_email,fit_reason,source_url,status,created_at,updated_at
  ) VALUES (@id,@name,@city,@region,@category,@websiteStatus,@contactPhone,@contactEmail,@fitReason,@sourceUrl,@status,@createdAt,@updatedAt)
  ON CONFLICT(id) DO UPDATE SET
    name=excluded.name, city=excluded.city, region=excluded.region, category=excluded.category,
    website_status=excluded.website_status, contact_phone=excluded.contact_phone, contact_email=excluded.contact_email,
    fit_reason=excluded.fit_reason, source_url=excluded.source_url, updated_at=excluded.updated_at`);
  const note = db.prepare(
    `INSERT INTO research_notes (id, lead_id, body, source, created_at) VALUES (?,?,?,?,?)`,
  );
  const ts = nowIso();
  let imported = 0;
  const tx = db.transaction(() => {
    for (const l of leads) {
      upsert.run({
        id: l.id,
        name: l.name,
        city: l.city ?? null,
        region: l.region ?? null,
        category: l.category ?? null,
        websiteStatus: l.websiteStatus ?? null,
        contactPhone: l.contactPhone ?? null,
        contactEmail: l.contactEmail ?? null,
        fitReason: l.fitReason ?? null,
        sourceUrl: l.sourceUrl ?? null,
        status: l.status ?? "new",
        createdAt: ts,
        updatedAt: ts,
      });
      note.run(id("rn"), l.id, l.fitReason || "Imported from seed", l.sourceUrl || "seed", ts);
      imported++;
    }
  });
  tx();
  writeAudit(db, { action: "research.import", meta: { imported } });
  return { imported };
}
