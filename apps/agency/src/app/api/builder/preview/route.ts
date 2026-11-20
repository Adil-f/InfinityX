import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { enqueueAndRun } from "@infinityx/orchestrator";
import { templatesRoot, previewsRoot, exportsRoot } from "@/lib/paths";

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const leadId = String(form.get("leadId") || "");
  const category = String(form.get("category") || "");
  const doExport = form.get("export") === "1";
  const { result } = enqueueAndRun(
    db(),
    "website_builder",
    { leadId, category: category || undefined, export: doExport },
    { templatesRoot: templatesRoot(), previewsRoot: previewsRoot(), exportsRoot: exportsRoot() },
  );
  const previewId = (result as { previewId: string }).previewId;
  return NextResponse.redirect(new URL(`/previews/${previewId}`, req.url), 303);
}
