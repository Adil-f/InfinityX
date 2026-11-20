import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { enqueueAndRun } from "@infinityx/orchestrator";
import { templatesRoot, previewsRoot, exportsRoot } from "@/lib/paths";

export async function GET() {
  return NextResponse.json(
    db().prepare(`SELECT d.*, l.name as lead_name FROM drafts d JOIN leads l ON l.id=d.lead_id ORDER BY d.created_at DESC`).all(),
  );
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const result = enqueueAndRun(
    db(),
    "email_draft",
    { leadId: body.leadId, channel: body.channel || "email" },
    { templatesRoot: templatesRoot(), previewsRoot: previewsRoot(), exportsRoot: exportsRoot() },
  );
  return NextResponse.json(result);
}
