"use client";

import { FormEvent, useEffect, useState } from "react";
import { useWorkspace } from "@/components/Shell";
import { api } from "@/lib/api";

type Source = {
  id: string;
  name: string;
  category: string;
  description: string;
  required_env: string[];
  missing_env: string[];
  enabled: boolean;
  configuration: string;
  last_health: string | null;
  last_error: string | null;
};

export function SourcesScreen() {
  const { token, can } = useWorkspace();
  const [rows, setRows] = useState<Source[]>([]);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");

  async function load() {
    setRows(await api<Source[]>("/api/v1/sources", {}, token));
  }
  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  async function probe(id: string) {
    setPending(id);
    setError("");
    try {
      const result = await api<{ status: string; detail: string }>(`/api/v1/sources/${id}/health`, { method: "POST" }, token);
      setError("");
      await load();
      setPending(`${id}: ${result.status}. ${result.detail}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Health check failed");
    }
  }

  async function toggle(source: Source) {
    await api(`/api/v1/sources/${source.id}`, { method: "PATCH", body: JSON.stringify({ enabled: !source.enabled }) }, token);
    await load();
  }

  return (
    <div>
      <h1 className="page-title">Source Management</h1>
      <p className="lede">Connectors declare their configuration, rate limit, and health. A missing key stays unavailable. Nothing here invents a response.</p>
      {error && <div className="error">{error}</div>}
      {pending && !error && <div className="note">{pending}</div>}
      <div className="grid-2">
        {rows.map((source) => (
          <article className="card" key={source.id}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h2 style={{ margin: 0 }}>{source.name}</h2>
              <span className={`badge ${source.configuration === "configured" ? "fact" : "warn"}`}>{source.configuration}</span>
            </div>
            <p>{source.description}</p>
            <p className="muted">{source.category}{source.required_env.length ? ` · requires ${source.required_env.join(", ")}` : ""}</p>
            {source.last_health && <p className="muted">Last probe: {source.last_health}{source.last_error ? ` — ${source.last_error}` : ""}</p>}
            <div className="cluster">
              {can("sources") && <button className="btn" onClick={() => void probe(source.id)}>Run health check</button>}
              {can("sources") && <button className="btn secondary" onClick={() => void toggle(source)}>{source.enabled ? "Disable" : "Enable"}</button>}
              {!can("sources") && <span className="muted">Health changes require the sources permission.</span>}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export function KeysScreen() {
  const { token, can } = useWorkspace();
  const [rows, setRows] = useState<{ id: string; name: string; prefix: string; scopes: string[]; revoked: boolean }[]>([]);
  const [name, setName] = useState("Integration");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setRows(await api("/api/v1/api-keys", {}, token));
  }
  useEffect(() => { if (can("apikeys")) load().catch((err) => setError(err.message)); }, [token]);

  async function create(event: FormEvent) {
    event.preventDefault();
    const created = await api<{ token: string }>("/api/v1/api-keys", { method: "POST", body: JSON.stringify({ name, scopes: ["search", "read"] }) }, token);
    setSecret(created.token);
    await load();
  }

  async function revoke(id: string) {
    await api(`/api/v1/api-keys/${id}`, { method: "DELETE" }, token);
    await load();
  }

  if (!can("apikeys")) return <div><h1 className="page-title">API Management</h1><div className="note">Your role cannot manage API keys.</div></div>;
  return (
    <div>
      <h1 className="page-title">API Management</h1>
      <p className="lede">Keys can search and read. They are shown once and cannot grant administration.</p>
      {error && <div className="error">{error}</div>}
      <form className="card cluster" onSubmit={create}>
        <label>Name<input value={name} onChange={(event) => setName(event.target.value)} required /></label>
        <button className="btn" type="submit">Create key</button>
      </form>
      {secret && <div className="note">Copy this token now. It will not be shown again.<div className="secret">{secret}</div></div>}
      <table className="table">
        <thead><tr><th>Name</th><th>Prefix</th><th>Scopes</th><th></th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.name}</td><td className="mono">{row.prefix}</td><td>{row.scopes.join(", ")}{row.revoked ? " · revoked" : ""}</td>
              <td>{!row.revoked && <button className="btn secondary" onClick={() => void revoke(row.id)}>Revoke</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

type Billing = {
  plan: string;
  credits_balance: number;
  stripe_configured: boolean;
  charged: boolean;
  plans: { id: string; label: string; credits: number; searches_per_minute: number; list_price_eur: number | null; note: string }[];
  ledger: { delta: number; reason: string; created_at: string }[];
};

export function BillingScreen() {
  const { token, can, refresh } = useWorkspace();
  const [data, setData] = useState<Billing | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setData(await api<Billing>("/api/v1/billing", {}, token));
  }
  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  async function checkout(plan: string) {
    setError("");
    const result = await api<{ status: string; message: string; url?: string; charged: boolean }>("/api/v1/billing/checkout", { method: "POST", body: JSON.stringify({ plan }) }, token);
    setMessage(result.message);
    if (result.url) window.location.href = result.url;
  }

  async function comp(plan: string) {
    const result = await api<{ charged: boolean; plan: string }>("/api/v1/billing/plan", { method: "POST", body: JSON.stringify({ plan }) }, token);
    setMessage(`Plan set to ${result.plan}. Charged: ${String(result.charged)}.`);
    await refresh();
    await load();
  }

  return (
    <div>
      <h1 className="page-title">Billing</h1>
      <p className="lede">Current plan {data?.plan}. Credits {data?.credits_balance}. Stripe configured: {String(data?.stripe_configured)}. No local charge is simulated.</p>
      {error && <div className="error">{error}</div>}
      {message && <div className="note">{message}</div>}
      <div className="grid-3">
        {data?.plans.map((plan) => (
          <article className="card" key={plan.id}>
            <h2>{plan.label}</h2>
            <p>{plan.list_price_eur === null ? "Contract" : `€${plan.list_price_eur} list price`}</p>
            <p className="muted">{plan.credits} credits · {plan.searches_per_minute}/min</p>
            <p className="muted">{plan.note}</p>
            {plan.id !== "free" && can("billing") && <button className="btn" onClick={() => void checkout(plan.id)}>Stripe checkout</button>}
            {can("admin") && <button className="btn secondary" onClick={() => void comp(plan.id)}>Set plan without payment</button>}
          </article>
        ))}
      </div>
      <section className="card">
        <h2>Ledger</h2>
        <table className="table">
          <tbody>{data?.ledger.map((row, index) => <tr key={index}><td>{row.delta}</td><td>{row.reason}</td><td>{new Date(row.created_at).toLocaleString()}</td></tr>)}</tbody>
        </table>
      </section>
    </div>
  );
}

export function AdminScreen() {
  const { token, can, me, refresh } = useWorkspace();
  const [users, setUsers] = useState<{ id: string; email: string; full_name: string; role: string; status: string; is_fixture: boolean }[]>([]);
  const [teams, setTeams] = useState<{ id: string; name: string; is_fixture: boolean; members: string[] }[]>([]);
  const [audit, setAudit] = useState<{ action: string; created_at: string; details: Record<string, unknown> }[]>([]);
  const [days, setDays] = useState(365);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("analyst");
  const [password, setPassword] = useState("Correct-Horse-12");
  const [team, setTeam] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    if (!can("admin")) return;
    setUsers(await api("/api/v1/admin/users", {}, token));
    setTeams(await api("/api/v1/admin/teams", {}, token));
    setAudit(await api("/api/v1/admin/audit", {}, token));
    const retention = await api<{ days: number }>("/api/v1/admin/retention", {}, token);
    setDays(retention.days);
  }
  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  if (!can("admin")) return <div><h1 className="page-title">Administration</h1><div className="note">Administration requires the admin permission.</div></div>;

  async function invite(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api("/api/v1/admin/users", { method: "POST", body: JSON.stringify({ email, full_name: name, role, password }) }, token);
      setMessage(`Invited ${email}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invite failed");
    }
  }

  async function changeRole(id: string, next: string) {
    try {
      await api(`/api/v1/admin/users/${id}`, { method: "PATCH", body: JSON.stringify({ role: next }) }, token);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Role change failed");
    }
  }

  return (
    <div>
      <h1 className="page-title">Administration</h1>
      <p className="lede">Users, teams, audit, retention, and GDPR controls for this organization.</p>
      {error && <div className="error">{error}</div>}
      {message && <div className="note">{message}</div>}
      <form className="card grid-2" onSubmit={invite}>
        <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Name<input value={name} onChange={(event) => setName(event.target.value)} required /></label>
        <label>Role
          <select value={role} onChange={(event) => setRole(event.target.value)}>
            {["analyst", "investigator", "viewer", "billing", "admin"].map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label>Temporary password<input value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        <button className="btn" type="submit">Invite user</button>
      </form>
      <table className="table">
        <thead><tr><th>User</th><th>Role</th><th>Status</th></tr></thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.full_name}<div className="muted">{user.email}{user.is_fixture ? " · development fixture" : ""}</div></td>
              <td>
                <select aria-label={`Role for ${user.email}`} value={user.role} onChange={(event) => void changeRole(user.id, event.target.value)}>
                  {["owner", "admin", "investigator", "analyst", "viewer", "billing"].map((item) => <option key={item}>{item}</option>)}
                </select>
              </td>
              <td>{user.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="card cluster" onSubmit={async (event) => { event.preventDefault(); await api("/api/v1/admin/teams", { method: "POST", body: JSON.stringify({ name: team }) }, token); setTeam(""); await load(); }}>
        <label>Team<input value={team} onChange={(event) => setTeam(event.target.value)} required /></label>
        <button className="btn" type="submit">Create team</button>
      </form>
      <ul>{teams.map((item) => <li key={item.id}>{item.name}{item.is_fixture ? " (development fixture)" : ""} · {item.members.length} members</li>)}</ul>
      <form className="card cluster" onSubmit={async (event) => { event.preventDefault(); const result = await api<{ expired_investigations: number }>("/api/v1/admin/retention", { method: "PUT", body: JSON.stringify({ days }) }, token); setMessage(`Retention set to ${result && days} days.`); }}>
        <label>Retention days<input type="number" min={7} max={3650} value={days} onChange={(event) => setDays(Number(event.target.value))} /></label>
        <button className="btn" type="submit">Save retention</button>
        <button className="btn secondary" type="button" onClick={async () => setMessage(JSON.stringify(await api("/api/v1/admin/retention/run", { method: "POST" }, token)))}>Run retention</button>
      </form>
      <div className="cluster">
        <button className="btn secondary" onClick={async () => {
          const exported = await api<unknown>("/api/v1/gdpr/export", { method: "POST" }, token);
          const blob = new Blob([JSON.stringify(exported, null, 2)], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = "infinityx-personal-data.json";
          link.click();
          URL.revokeObjectURL(url);
        }}>Export my data</button>
      </div>
      <form className="card" onSubmit={async (event) => {
        event.preventDefault();
        if (confirm !== me?.email) { setError("Type your email to confirm deletion."); return; }
        await api("/api/v1/gdpr/delete", { method: "POST" }, token);
        sessionStorage.removeItem("ix_token");
        window.location.href = "/login";
      }}>
        <label>Delete my account by typing the email<input value={confirm} onChange={(event) => setConfirm(event.target.value)} /></label>
        <button className="btn" type="submit">Anonymize my account</button>
      </form>
      <section className="card">
        <h2>Audit</h2>
        <table className="table">
          <tbody>{audit.slice(0, 30).map((row, index) => <tr key={index}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.action}</td><td className="mono">{JSON.stringify(row.details)}</td></tr>)}</tbody>
        </table>
      </section>
    </div>
  );
}
