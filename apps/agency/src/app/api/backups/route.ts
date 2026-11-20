import { NextResponse } from "next/server";
import { spawnSync } from "child_process";
import path from "path";
import { repoRoot } from "@/lib/paths";

export async function POST() {
  const script = path.join(repoRoot(), "packages/scripts/backup_db.py");
  const res = spawnSync("python3", [script], { encoding: "utf8" });
  return NextResponse.json({ status: res.status, out: res.stdout, err: res.stderr });
}

export async function GET() {
  const { db } = await import("@/lib/db");
  return NextResponse.json(db().prepare(`SELECT * FROM backup_runs ORDER BY created_at DESC`).all());
}
