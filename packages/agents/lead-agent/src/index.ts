import type Database from "better-sqlite3";
import { nowIso, writeAudit } from "../../../db/src/client";

export function runLeadAgent(db: Database.Database, payload: Record<string, unknown>) {
  const leadId = String(payload.leadId || "");
  const status = String(payload.status || "");
  if (!leadId || !status) throw new Error("leadId and status required");
  const info = db.prepare(`UPDATE leads SET status=?, updated_at=? WHERE id=?`).run(status, nowIso(), leadId);
  if (info.changes === 0) throw new Error("Lead not found");
  writeAudit(db, { action: "lead.status", resourceType: "lead", resourceId: leadId, meta: { status } });
  return { leadId, status };
}
