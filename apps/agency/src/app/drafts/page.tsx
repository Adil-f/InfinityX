import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export default function DraftsPage() {
  const drafts = db().prepare(
    `SELECT d.*, l.name as lead_name FROM drafts d JOIN leads l ON l.id=d.lead_id ORDER BY d.created_at DESC`,
  ).all() as Array<Record<string, unknown>>;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Drafts</h1>
      <p className="text-sm text-black/60">Local drafts only. Sending requires approval and is not wired in Phase 2.</p>
      {drafts.map((d) => (
        <article key={String(d.id)} className="card space-y-2">
          <div className="flex justify-between gap-2 text-sm">
            <strong>{String(d.lead_name)}</strong>
            <span>{String(d.channel)} · {String(d.status)}</span>
          </div>
          <div className="text-sm font-medium">{String(d.subject || "")}</div>
          <pre className="whitespace-pre-wrap rounded bg-black/[0.03] p-3 text-xs">{String(d.body)}</pre>
          <form action="/api/approvals" method="post" className="flex flex-wrap gap-2">
            <input type="hidden" name="actionType" value="send_email" />
            <input type="hidden" name="resourceType" value="draft" />
            <input type="hidden" name="resourceId" value={String(d.id)} />
            <button className="btn-secondary" type="submit">Request send approval</button>
          </form>
        </article>
      ))}
    </div>
  );
}
