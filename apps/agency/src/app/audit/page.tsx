import { db } from "@/lib/db";
export const dynamic = "force-dynamic";
export default function AuditPage() {
  const rows = db().prepare(`SELECT * FROM audit_logs ORDER BY at DESC LIMIT 200`).all() as Array<Record<string, unknown>>;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Audit log</h1>
      <div className="card overflow-x-auto">
        <table>
          <thead><tr><th>At</th><th>Actor</th><th>Action</th><th>Resource</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={String(r.id)}>
                <td className="whitespace-nowrap text-xs">{String(r.at)}</td>
                <td>{String(r.actor)}</td>
                <td>{String(r.action)}</td>
                <td className="text-xs">{String(r.resource_type || "")} {String(r.resource_id || "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
