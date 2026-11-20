import { NextRequest, NextResponse } from "next/server";
import { composeSite } from "@infinityx/website-builder";
import { templatesRoot } from "@/lib/paths";
import { db } from "@/lib/db";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const lead = db().prepare(`SELECT * FROM leads WHERE id=?`).get(body.leadId) as Record<string, unknown> | undefined;
  if (!lead) return NextResponse.json({ error: "Lead not found" }, { status: 404 });
  const composition = composeSite(templatesRoot(), {
    id: String(lead.id),
    name: String(lead.name),
    city: lead.city as string,
    category: (body.category as string) || (lead.category as string),
    fitReason: lead.fit_reason as string,
  });
  return NextResponse.json(composition);
}
