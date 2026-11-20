import { db } from "@/lib/db";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function BuilderPage({
  searchParams,
}: {
  searchParams: Promise<{ leadId?: string }>;
}) {
  const sp = await searchParams;
  const leads = db().prepare(`SELECT id, name, category, city FROM leads ORDER BY name`).all() as Array<{
    id: string; name: string; category: string | null; city: string | null;
  }>;
  const previews = db().prepare(
    `SELECT p.*, sb.layout_family, sb.brand_system_id, l.name as lead_name
     FROM previews p
     JOIN site_builds sb ON sb.id = p.build_id
     JOIN leads l ON l.id = sb.lead_id
     ORDER BY p.created_at DESC LIMIT 20`,
  ).all() as Array<Record<string, unknown>>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Website Builder</h1>
      <p className="text-sm text-black/60">
        Compositional layouts (6+ families). Not logo/color-only clones. Forms disabled by default.
      </p>
      <form className="card space-y-3" action="/api/builder/preview" method="post">
        <label className="block text-sm">Lead
          <select name="leadId" defaultValue={sp.leadId || leads[0]?.id || ""}>
            {leads.map((l) => (
              <option key={l.id} value={l.id}>{l.name} ({l.category || "?"} · {l.city || "?"})</option>
            ))}
          </select>
        </label>
        <label className="block text-sm">Category override (optional)
          <select name="category" defaultValue="">
            <option value="">Use lead category</option>
            {["ristorante","negozio","artigiano","studio","servizi","ospitalita"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" name="export" value="1" /> Also create ZIP export
        </label>
        <button className="btn" type="submit">Generate preview</button>
      </form>

      <div className="card">
        <h2 className="mb-2 font-medium">Recent previews</h2>
        <table>
          <thead><tr><th>Lead</th><th>Layout</th><th>Brand</th><th>Tests</th><th></th></tr></thead>
          <tbody>
            {previews.map((p) => (
              <tr key={String(p.id)}>
                <td>{String(p.lead_name)}</td>
                <td>{String(p.layout_family)}</td>
                <td>{String(p.brand_system_id)}</td>
                <td>{String(p.last_test_status)}</td>
                <td><Link href={`/previews/${p.id}`}>Open</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
