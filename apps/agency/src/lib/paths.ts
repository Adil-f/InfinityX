import path from "path";

export function repoRoot(): string {
  // apps/agency -> repo root
  return path.resolve(process.cwd(), "../..");
}

export function templatesRoot(): string {
  return process.env.TEMPLATES_ROOT
    ? path.resolve(process.cwd(), process.env.TEMPLATES_ROOT)
    : path.join(repoRoot(), "templates");
}

export function previewsRoot(): string {
  return process.env.PREVIEWS_ROOT
    ? path.resolve(process.cwd(), process.env.PREVIEWS_ROOT)
    : path.join(repoRoot(), "data/previews");
}

export function exportsRoot(): string {
  return process.env.EXPORTS_ROOT
    ? path.resolve(process.cwd(), process.env.EXPORTS_ROOT)
    : path.join(repoRoot(), "data/exports");
}

export function backupsRoot(): string {
  return process.env.BACKUPS_ROOT
    ? path.resolve(process.cwd(), process.env.BACKUPS_ROOT)
    : path.join(repoRoot(), "data/backups");
}

export function dbPath(): string {
  return process.env.DATABASE_PATH
    ? path.resolve(process.cwd(), process.env.DATABASE_PATH)
    : path.join(repoRoot(), "data/agency.db");
}

export function seedPath(): string {
  return path.join(repoRoot(), "data/seed/leads.seed.json");
}
