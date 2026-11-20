import { NextRequest, NextResponse } from "next/server";
import { expectedSecret, ownerCookieHeader } from "@/lib/auth";
import { writeAudit } from "@infinityx/db";
import { db } from "@/lib/db";

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const secret = String(form.get("secret") || "");
  const res = NextResponse.redirect(new URL("/approvals", req.url), 303);
  if (secret === expectedSecret()) {
    res.headers.set("Set-Cookie", ownerCookieHeader(secret));
    writeAudit(db(), { actor: "owner", action: "auth.login" });
  } else {
    writeAudit(db(), { actor: "anonymous", action: "auth.login_failed" });
  }
  return res;
}
