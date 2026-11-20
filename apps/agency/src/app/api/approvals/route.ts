import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { id, nowIso, writeAudit } from "@infinityx/db";

export async function GET() {
  return NextResponse.json(db().prepare(`SELECT * FROM approval_requests ORDER BY created_at DESC`).all());
}

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const actionType = String(form.get("actionType") || "other");
  const resourceType = String(form.get("resourceType") || "");
  const resourceId = String(form.get("resourceId") || "");
  const approvalId = id("apr");
  db().prepare(
    `INSERT INTO approval_requests (id, action_type, resource_type, resource_id, payload_json, status, requested_by, created_at)
     VALUES (?,?,?,?,?,?,?,?)`,
  ).run(approvalId, actionType, resourceType, resourceId, null, "pending", "owner", nowIso());
  writeAudit(db(), { action: "approval.requested", resourceType: "approval", resourceId: approvalId, meta: { actionType } });
  return NextResponse.redirect(new URL("/approvals", req.url), 303);
}
