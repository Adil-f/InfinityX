import { db } from "@/lib/db";
export const dynamic = "force-dynamic";
export default function JobsPage() {
  const rows = db().prepare(`SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100`).all() as Array<Record<string, unknown>>;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Jobs / Orchestrator</h1>
      <div className="card overflow-x-auto">
        <table>
          <thead><tr><th>Created</th><th>Agent</th><th>Status</th><th>Error</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={String(r.id)}>
                <td className="text-xs">{String(r.created_at)}</td>
                <td>{String(r.agent_id)}</td>
                <td>{String(r.status)}</td>
                <td className="text-xs">{String(r.error || "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
