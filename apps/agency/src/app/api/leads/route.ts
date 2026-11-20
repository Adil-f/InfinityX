import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { enqueueAndRun } from "@infinityx/orchestrator";
import { templatesRoot, previewsRoot, exportsRoot } from "@/lib/paths";

export async function GET() {
  const leads = db().prepare(`SELECT * FROM leads ORDER BY updated_at DESC`).all();
  return NextResponse.json(leads);
}

export async function PATCH(req: NextRequest) {
  const body = await req.json();
  const result = enqueueAndRun(
    db(),
    "lead",
    { leadId: body.leadId, status: body.status },
    { templatesRoot: templatesRoot(), previewsRoot: previewsRoot(), exportsRoot: exportsRoot() },
  );
  return NextResponse.json(result);
}
