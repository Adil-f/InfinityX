import { db } from "@/lib/db";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default function DashboardPage() {
  const database = db();
  const leads = database.prepare(`SELECT COUNT(*) as c FROM leads`).get() as { c: number };
  const drafts = database.prepare(`SELECT COUNT(*) as c FROM drafts`).get() as { c: number };
  const pending = database.prepare(`SELECT COUNT(*) as c FROM approval_requests WHERE status='pending'`).get() as { c: number };
  const previews = database.prepare(`SELECT COUNT(*) as c FROM previews`).get() as { c: number };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-3xl">Agency dashboard</h1>
        <p className="text-sm text-black/60">Local orchestration · SQLite · approval gates</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card"><div className="text-2xl font-semibold">{leads.c}</div><div className="text-sm">Leads</div></div>
        <div className="card"><div className="text-2xl font-semibold">{drafts.c}</div><div className="text-sm">Drafts</div></div>
        <div className="card"><div className="text-2xl font-semibold">{pending.c}</div><div className="text-sm">Pending approvals</div></div>
        <div className="card"><div className="text-2xl font-semibold">{previews.c}</div><div className="text-sm">Previews</div></div>
      </div>
      <div className="card space-y-2">
        <h2 className="font-medium">Quick actions</h2>
        <div className="flex flex-wrap gap-2">
          <Link className="btn" href="/leads">Manage leads</Link>
          <Link className="btn-secondary" href="/builder">Build website</Link>
          <Link className="btn-secondary" href="/approvals">Approvals</Link>
        </div>
      </div>
    </div>
  );
}
