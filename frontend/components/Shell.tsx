"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";
import { api, Me } from "@/lib/api";

type Investigation = { id: string; title: string; status: string; purpose: string; lawful_basis: string };

type WorkspaceValue = {
  token: string;
  me: Me | null;
  investigations: Investigation[];
  investigationId: string;
  setInvestigationId: (id: string) => void;
  refresh: () => Promise<void>;
  can: (permission: string) => boolean;
};

const WorkspaceContext = createContext<WorkspaceValue | null>(null);
export function useWorkspace() {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("Workspace missing");
  return value;
}

const NAV = [
  ["Investigate", [
    ["/overview", "Overview"],
    ["/search", "Universal Search"],
    ["/ai", "AI Investigator"],
    ["/reports", "Reports"],
  ]],
  ["Intelligence", [
    ["/phone", "Phone"],
    ["/cnic", "CNIC"],
    ["/email", "Email"],
    ["/username", "Username"],
    ["/social", "Social"],
    ["/ip", "IP"],
    ["/domain", "Domain"],
    ["/threat", "Threat"],
    ["/forensics", "Digital Forensics"],
  ]],
  ["Platform", [
    ["/sources", "Source Management"],
    ["/api-keys", "API Management"],
    ["/billing", "Billing"],
    ["/admin", "Administration"],
  ]],
] as const;

function Logo() {
  return (
    <svg width="36" height="36" viewBox="0 0 300 300" aria-hidden="true">
      <path d="M 60 150 Q 90 50, 150 150 Q 210 250, 240 150" stroke="#c4b5fd" strokeWidth="28" fill="none" />
      <path d="M 240 150 Q 210 50, 150 150 Q 90 250, 60 150" stroke="#67e8f9" strokeWidth="28" fill="none" />
    </svg>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [investigationId, setInvestigationId] = useState("");
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [purpose, setPurpose] = useState("Authorized security investigation");
  const [basis, setBasis] = useState("legitimate_interest");
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);

  async function refresh(current = token) {
    if (!current) return;
    const profile = await api<Me>("/api/v1/auth/me", {}, current);
    setMe(profile);
    const rows = await api<Investigation[]>("/api/v1/investigations", {}, current);
    setInvestigations(rows);
    setInvestigationId((currentId) => currentId || rows[0]?.id || "");
  }

  useEffect(() => {
    const saved = sessionStorage.getItem("ix_token");
    const theme = localStorage.getItem("ix-theme") || "dark";
    document.documentElement.dataset.theme = theme;
    if (!saved) {
      router.replace("/login");
      return;
    }
    setToken(saved);
    const storedCase = sessionStorage.getItem("ix_case") || "";
    setInvestigationId(storedCase);
    refresh(saved).catch(() => {
      sessionStorage.removeItem("ix_token");
      router.replace("/login");
    }).finally(() => setReady(true));
  }, [router]);

  useEffect(() => {
    if (investigationId) sessionStorage.setItem("ix_case", investigationId);
  }, [investigationId]);

  if (!ready || !token) return <div className="content">Loading session…</div>;

  async function createCase(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const created = await api<{ id: string }>("/api/v1/investigations", {
        method: "POST",
        body: JSON.stringify({ title, purpose, lawful_basis: basis }),
      }, token);
      setTitle("");
      setCreating(false);
      await refresh(token);
      setInvestigationId(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the investigation");
    }
  }

  function toggleTheme() {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("ix-theme", next);
  }

  const value: WorkspaceValue = {
    token,
    me,
    investigations,
    investigationId,
    setInvestigationId,
    refresh: () => refresh(token),
    can: (permission) => Boolean(me?.permissions.includes(permission)),
  };

  return (
    <WorkspaceContext.Provider value={value}>
      <div className="shell">
        <aside className="sidebar">
          <div className="brand">
            <Logo />
            <div>
              <strong>INFINITY X</strong>
              <span>Global OSINT</span>
            </div>
          </div>
          {NAV.map(([group, links]) => (
            <div key={group}>
              <div className="nav-group">{group}</div>
              {links.map(([href, label]) => (
                <Link key={href} href={href} className={pathname === href ? "nav-link active" : "nav-link"}>{label}</Link>
              ))}
            </div>
          ))}
        </aside>
        <section className="main">
          <header className="topbar">
            <div>
              <strong>{me?.org_name}</strong>
              <div className="muted">{me?.plan} plan · {me?.credits_balance} credits · {me?.role}</div>
            </div>
            <div className="top-actions">
              <select aria-label="Active investigation" value={investigationId} onChange={(event) => setInvestigationId(event.target.value)}>
                <option value="">No investigation</option>
                {investigations.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
              </select>
              {value.can("investigate") && <button className="btn secondary" onClick={() => setCreating((open) => !open)}>New case</button>}
              <button className="btn secondary" onClick={toggleTheme}>Theme</button>
              <button className="btn secondary" onClick={() => { sessionStorage.removeItem("ix_token"); router.replace("/login"); }}>Sign out</button>
            </div>
          </header>
          <div className="content">
            {me?.is_fixture && <div className="banner">Signed in with a development fixture account. Search results are live or explicitly unavailable. They are not fixture intelligence.</div>}
            {creating && (
              <form className="card grid-2" onSubmit={createCase}>
                <label>Title<input value={title} onChange={(event) => setTitle(event.target.value)} required minLength={3} /></label>
                <label>Lawful basis
                  <select value={basis} onChange={(event) => setBasis(event.target.value)}>
                    <option value="legitimate_interest">Legitimate interest</option>
                    <option value="consent">Consent</option>
                    <option value="legal_obligation">Legal obligation</option>
                    <option value="contract">Contract</option>
                    <option value="public_task">Public task</option>
                  </select>
                </label>
                <label>Purpose<input value={purpose} onChange={(event) => setPurpose(event.target.value)} required minLength={8} /></label>
                <div className="cluster"><button className="btn" type="submit">Create investigation</button></div>
                {error && <div className="error">{error}</div>}
              </form>
            )}
            {children}
            <p className="muted">Authorized use only. Public sources and configured providers. No covert surveillance, subscriber identification, or private identity registry.</p>
          </div>
        </section>
      </div>
    </WorkspaceContext.Provider>
  );
}
