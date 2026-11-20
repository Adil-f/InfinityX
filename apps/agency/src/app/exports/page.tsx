import { db } from "@/lib/db";
export const dynamic = "force-dynamic";
export default function ExportsPage() {
  const rows = db().prepare(`SELECT * FROM export_artifacts ORDER BY created_at DESC`).all() as Array<Record<string, unknown>>;
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Exports</h1>
      <p className="text-sm text-black/60">Production-ready static ZIPs on local disk only (not published).</p>
      <div className="card">
        <table>
          <thead><tr><th>Created</th><th>Path</th><th>Checksum</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={String(r.id)}>
                <td className="text-xs">{String(r.created_at)}</td>
                <td className="text-xs break-all">{String(r.path)}</td>
                <td className="text-xs">{String(r.checksum || "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
