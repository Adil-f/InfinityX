import { db } from "@/lib/db";
import fs from "fs";
import path from "path";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function PreviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const row = db().prepare(`SELECT * FROM previews WHERE id=?`).get(id) as
    | { id: string; path: string; last_test_status: string | null }
    | undefined;
  if (!row) notFound();
  const indexPath = path.join(row.path, "index.html");
  if (!fs.existsSync(indexPath)) notFound();
  const html = fs.readFileSync(indexPath, "utf8");
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Preview {id}</h1>
        <p className="text-sm">Tests: {row.last_test_status || "n/a"}</p>
      </div>
      <iframe title="site-preview" className="h-[75vh] w-full rounded-xl border border-black/10 bg-white" srcDoc={html} />
      <p className="text-xs text-black/50">Local preview only — not published.</p>
    </div>
  );
}
