import type Database from "better-sqlite3";
import { id, nowIso, writeAudit } from "../../../db/src/client";

export function runEmailDraftAgent(db: Database.Database, payload: Record<string, unknown>) {
  const leadId = String(payload.leadId || "");
  const channel = String(payload.channel || "email");
  const lead = db.prepare(`SELECT * FROM leads WHERE id=?`).get(leadId) as
    | { name: string; city: string | null }
    | undefined;
  if (!lead) throw new Error("Lead not found");
  const subject = `Un sito semplice per ${lead.name}?`;
  const body = `Ciao,\n\nsono Infinity X. Ho notato ${lead.name}${lead.city ? " a " + lead.city : ""}: online sembra mancare un sito chiaro.\n\nPossiamo preparare una bozza gratuita. Nessun impegno.\n\n(Bozza locale — invio esterno non abilitato in Phase 2.)\n`;
  const draftId = id("draft");
  db.prepare(
    `INSERT INTO drafts (id, lead_id, channel, subject, body, status, created_at) VALUES (?,?,?,?,?,?,?)`,
  ).run(draftId, leadId, channel, subject, body, "draft", nowIso());
  writeAudit(db, { action: "draft.create", resourceType: "draft", resourceId: draftId });
  return { draftId, subject };
}
