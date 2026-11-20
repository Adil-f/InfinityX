import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { enqueueAndRun } from "@infinityx/orchestrator";
import { templatesRoot, previewsRoot, exportsRoot } from "@/lib/paths";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const result = enqueueAndRun(
    db(),
    "website_builder",
    { leadId: body.leadId, category: body.category, export: true },
    { templatesRoot: templatesRoot(), previewsRoot: previewsRoot(), exportsRoot: exportsRoot() },
  );
  return NextResponse.json(result);
}
