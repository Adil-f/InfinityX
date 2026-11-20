import { db } from "@/lib/db";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default function LeadsPage() {
  const leads = db().prepare(`SELECT * FROM leads ORDER BY updated_at DESC`).all() as Array<Record<string, unknown>>;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Leads</h1>
        <form action="/api/research" method="post">
          <button className="btn" type="submit">Import seed (research agent)</button>
        </form>
      </div>
      <div className="card overflow-x-auto">
        <table>
          <thead>
            <tr><th>Name</th><th>City</th><th>Category</th><th>Status</th><th>Contact</th><th></th></tr>
          </thead>
          <tbody>
            {leads.map((l) => (
              <tr key={String(l.id)}>
                <td>{String(l.name)}</td>
                <td>{String(l.city || "")}</td>
                <td>{String(l.category || "")}</td>
                <td>{String(l.status)}</td>
                <td className="text-xs">{String(l.contact_email || l.contact_phone || "non trovato")}</td>
                <td><Link href={`/builder?leadId=${l.id}`}>Build</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
        {leads.length === 0 && <p className="text-sm text-black/60">No leads yet. Import seed.</p>}
      </div>
    </div>
  );
}
