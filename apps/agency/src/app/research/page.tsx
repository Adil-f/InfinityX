import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export default function ResearchPage() {
  const notes = db().prepare(
    `SELECT rn.*, l.name as lead_name FROM research_notes rn LEFT JOIN leads l ON l.id = rn.lead_id ORDER BY rn.created_at DESC LIMIT 100`,
  ).all() as Array<Record<string, unknown>>;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Research notes</h1>
      <div className="space-y-3">
        {notes.map((n) => (
          <article key={String(n.id)} className="card">
            <div className="text-sm font-medium">{String(n.lead_name || n.lead_id)}</div>
            <p className="text-sm">{String(n.body)}</p>
            <p className="text-xs text-black/50">{String(n.source || "")}</p>
          </article>
        ))}
        {notes.length === 0 && <p className="text-sm text-black/60">No research notes. Import leads first.</p>}
      </div>
    </div>
  );
}
