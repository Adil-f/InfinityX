import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export default function ApprovalsPage() {
  const rows = db().prepare(`SELECT * FROM approval_requests ORDER BY created_at DESC`).all() as Array<Record<string, unknown>>;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Approval dashboard</h1>
      <p className="text-sm text-black/60">Owner secret required to decide. External transports remain unwired.</p>
      <div className="card space-y-2">
        <h2 className="font-medium">Login (local)</h2>
        <form action="/api/auth/login" method="post" className="flex flex-wrap gap-2">
          <input name="secret" type="password" placeholder="AGENCY_OWNER_SECRET" />
          <button className="btn" type="submit">Set owner session</button>
        </form>
      </div>
      {rows.map((r) => (
        <article key={String(r.id)} className="card space-y-2">
          <div className="text-sm"><strong>{String(r.action_type)}</strong> · {String(r.status)}</div>
          <div className="text-xs text-black/60">{String(r.resource_type)} {String(r.resource_id)}</div>
          {r.status === "pending" && (
            <div className="flex gap-2">
              <form action={`/api/approvals/${r.id}/decide`} method="post">
                <input type="hidden" name="decision" value="approved" />
                <button className="btn" type="submit">Approve</button>
              </form>
              <form action={`/api/approvals/${r.id}/decide`} method="post">
                <input type="hidden" name="decision" value="rejected" />
                <button className="btn-secondary" type="submit">Reject</button>
              </form>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}
