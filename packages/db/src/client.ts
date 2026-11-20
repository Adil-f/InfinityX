import Database from "better-sqlite3";
import fs from "fs";
import path from "path";
import { randomUUID } from "crypto";

const SCHEMA = `PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT,
  region TEXT,
  category TEXT,
  website_status TEXT,
  contact_phone TEXT,
  contact_email TEXT,
  fit_reason TEXT,
  source_url TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_notes (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  source TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS drafts (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  channel TEXT NOT NULL,
  subject TEXT,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approval_requests (
  id TEXT PRIMARY KEY,
  action_type TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  payload_json TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  requested_by TEXT,
  decided_by TEXT,
  decided_at TEXT,
  note TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  at TEXT NOT NULL,
  actor TEXT,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  meta_json TEXT
);

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  lead_id TEXT,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  payload_json TEXT,
  status TEXT NOT NULL DEFAULT 'queued',
  result_json TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS site_builds (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  layout_family TEXT NOT NULL,
  brand_system_id TEXT NOT NULL,
  section_graph_json TEXT NOT NULL,
  page_graph_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS previews (
  id TEXT PRIMARY KEY,
  build_id TEXT NOT NULL REFERENCES site_builds(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  last_test_status TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_artifacts (
  id TEXT PRIMARY KEY,
  build_id TEXT NOT NULL REFERENCES site_builds(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  checksum TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backup_runs (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  checksum TEXT NOT NULL,
  created_at TEXT NOT NULL
);
`;

let _db: Database.Database | null = null;

export function resolveDbPath(explicit?: string): string {
  if (explicit) return path.resolve(explicit);
  if (process.env.DATABASE_PATH) {
    const p = process.env.DATABASE_PATH;
    return path.isAbsolute(p) ? p : path.resolve(process.cwd(), p);
  }
  // default: repo data/ from apps/agency cwd
  return path.resolve(process.cwd(), "../../data/agency.db");
}

export function getDb(dbPath?: string): Database.Database {
  if (_db) return _db;
  const resolved = resolveDbPath(dbPath);
  fs.mkdirSync(path.dirname(resolved), { recursive: true });
  _db = new Database(resolved);
  _db.pragma("journal_mode = WAL");
  _db.pragma("foreign_keys = ON");
  _db.exec(SCHEMA);
  seedAgents(_db);
  try {
    fs.chmodSync(resolved, 0o600);
  } catch {
    /* ignore */
  }
  return _db;
}

export function closeDb(): void {
  if (_db) {
    _db.close();
    _db = null;
  }
}

export function resetDbForTests(dbPath: string): Database.Database {
  closeDb();
  if (fs.existsSync(dbPath)) fs.unlinkSync(dbPath);
  return getDb(dbPath);
}

function seedAgents(db: Database.Database) {
  const agents = [
    ["research", "Research Agent"],
    ["lead", "Lead Agent"],
    ["website_builder", "Website Builder Agent"],
    ["email_draft", "Email Draft Agent"],
    ["qa", "QA Agent"],
    ["orchestrator", "Orchestrator"],
  ];
  const stmt = db.prepare(
    "INSERT OR IGNORE INTO agents (id, name, enabled) VALUES (?, ?, 1)",
  );
  for (const [id, name] of agents) stmt.run(id, name);
}

export function nowIso(): string {
  return new Date().toISOString();
}

export function id(prefix = ""): string {
  return prefix ? `${prefix}_${randomUUID()}` : randomUUID();
}

export function writeAudit(
  db: Database.Database,
  input: {
    actor?: string;
    action: string;
    resourceType?: string;
    resourceId?: string;
    meta?: unknown;
  },
) {
  db.prepare(
    `INSERT INTO audit_logs (id, at, actor, action, resource_type, resource_id, meta_json)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
  ).run(
    id("aud"),
    nowIso(),
    input.actor ?? "system",
    input.action,
    input.resourceType ?? null,
    input.resourceId ?? null,
    input.meta ? JSON.stringify(input.meta) : null,
  );
}
