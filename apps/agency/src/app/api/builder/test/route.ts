import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { db } from "@/lib/db";
import { formSubmitDisabled, hasSeoBasics } from "@infinityx/website-builder";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const preview = db().prepare(`SELECT * FROM previews WHERE id=?`).get(body.previewId) as
    | { id: string; path: string }
    | undefined;
  if (!preview) return NextResponse.json({ error: "not found" }, { status: 404 });
  const html = fs.readFileSync(path.join(preview.path, "index.html"), "utf8");
  const contactPath = path.join(preview.path, "contact.html");
  const contactHtml = fs.existsSync(contactPath) ? fs.readFileSync(contactPath, "utf8") : html;
  const result = {
    seo: hasSeoBasics(html),
    formDisabled: formSubmitDisabled(contactHtml),
    hasSitemap: fs.existsSync(path.join(preview.path, "sitemap.xml")),
  };
  const status = Object.values(result).every(Boolean) ? "passed" : "failed";
  db().prepare(`UPDATE previews SET last_test_status=? WHERE id=?`).run(status, preview.id);
  return NextResponse.json({ status, result });
}
