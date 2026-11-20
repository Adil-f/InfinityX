import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { nowIso, writeAudit } from "@infinityx/db";
import { isOwnerAuthenticated } from "@/lib/auth";
import { sendEmail } from "@/lib/integrations";

export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  if (!(await isOwnerAuthenticated())) {
    return NextResponse.redirect(new URL("/approvals?error=auth", req.url), 303);
  }
  const form = await req.formData();
  const decision = String(form.get("decision") || "");
  if (decision !== "approved" && decision !== "rejected") {
    return NextResponse.json({ error: "invalid decision" }, { status: 400 });
  }
  db().prepare(
    `UPDATE approval_requests SET status=?, decided_by=?, decided_at=? WHERE id=?`,
  ).run(decision, "owner", nowIso(), id);
  writeAudit(db(), { actor: "owner", action: `approval.${decision}`, resourceType: "approval", resourceId: id });

  // Even if approved, transport stays blocked — demonstrate gate.
  if (decision === "approved") {
    const row = db().prepare(`SELECT * FROM approval_requests WHERE id=?`).get(id) as {
      action_type: string;
      resource_id: string | null;
      status: string;
    };
    if (row.action_type === "send_email") {
      try {
        await sendEmail({
          to: "nobody@example.com",
          subject: "blocked",
          body: "blocked",
          approvalStatus: "approved",
        });
      } catch (e) {
        writeAudit(db(), {
          actor: "system",
          action: "send.blocked_transport",
          resourceType: "approval",
          resourceId: id,
          meta: { message: e instanceof Error ? e.message : String(e) },
        });
      }
    }
  }

  return NextResponse.redirect(new URL("/approvals", req.url), 303);
}
