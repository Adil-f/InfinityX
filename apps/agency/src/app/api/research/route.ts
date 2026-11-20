import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { enqueueAndRun } from "@infinityx/orchestrator";
import { seedPath, templatesRoot, previewsRoot, exportsRoot } from "@/lib/paths";

export async function POST() {
  const result = enqueueAndRun(
    db(),
    "research",
    { seedPath: seedPath() },
    { templatesRoot: templatesRoot(), previewsRoot: previewsRoot(), exportsRoot: exportsRoot() },
  );
  return NextResponse.redirect(new URL("/leads", process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"), 303);
}
