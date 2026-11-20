import type Database from "better-sqlite3";
import { id, nowIso, writeAudit } from "../../db/src/client";
import { runResearchAgent } from "../../agents/research-agent/src/index";
import { runLeadAgent } from "../../agents/lead-agent/src/index";
import { runWebsiteBuilderAgent } from "../../agents/website-builder-agent/src/index";
import { runEmailDraftAgent } from "../../agents/email-draft-agent/src/index";
import { runQaAgent } from "../../agents/qa-agent/src/index";

export type JobPayload = Record<string, unknown>;

export function enqueueJob(db: Database.Database, agentId: string, payload: JobPayload): string {
  const jobId = id("job");
  const ts = nowIso();
  db.prepare(
    `INSERT INTO jobs (id, agent_id, payload_json, status, created_at, updated_at) VALUES (?,?,?,?,?,?)`,
  ).run(jobId, agentId, JSON.stringify(payload), "queued", ts, ts);
  writeAudit(db, { action: "job.enqueue", resourceType: "job", resourceId: jobId, meta: { agentId } });
  return jobId;
}

export function processJob(db: Database.Database, jobId: string, paths: {
  templatesRoot: string;
  previewsRoot: string;
  exportsRoot: string;
}): unknown {
  const job = db.prepare(`SELECT * FROM jobs WHERE id = ?`).get(jobId) as
    | { id: string; agent_id: string; payload_json: string; status: string }
    | undefined;
  if (!job) throw new Error("Job not found");
  db.prepare(`UPDATE jobs SET status=?, updated_at=? WHERE id=?`).run("running", nowIso(), jobId);
  const payload = JSON.parse(job.payload_json || "{}") as JobPayload;
  try {
    let result: unknown;
    switch (job.agent_id) {
      case "research":
        result = runResearchAgent(db, payload);
        break;
      case "lead":
        result = runLeadAgent(db, payload);
        break;
      case "website_builder":
        result = runWebsiteBuilderAgent(db, payload, paths);
        break;
      case "email_draft":
        result = runEmailDraftAgent(db, payload);
        break;
      case "qa":
        result = runQaAgent(payload);
        break;
      default:
        throw new Error(`Unknown agent: ${job.agent_id}`);
    }
    db.prepare(`UPDATE jobs SET status=?, result_json=?, updated_at=? WHERE id=?`).run(
      "succeeded",
      JSON.stringify(result),
      nowIso(),
      jobId,
    );
    writeAudit(db, { action: "job.succeeded", resourceType: "job", resourceId: jobId });
    return result;
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    db.prepare(`UPDATE jobs SET status=?, error=?, updated_at=? WHERE id=?`).run(
      "failed",
      msg,
      nowIso(),
      jobId,
    );
    writeAudit(db, { action: "job.failed", resourceType: "job", resourceId: jobId, meta: { msg } });
    throw e;
  }
}

export function enqueueAndRun(
  db: Database.Database,
  agentId: string,
  payload: JobPayload,
  paths: { templatesRoot: string; previewsRoot: string; exportsRoot: string },
) {
  const jobId = enqueueJob(db, agentId, payload);
  const result = processJob(db, jobId, paths);
  return { jobId, result };
}
