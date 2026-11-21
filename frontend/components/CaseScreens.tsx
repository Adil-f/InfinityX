"use client";

import { FormEvent, useEffect, useState } from "react";
import { Findings } from "@/components/Findings";
import { GraphData, GraphView, RELATIONS } from "@/components/GraphView";
import { useWorkspace } from "@/components/Shell";
import { api, Finding } from "@/lib/api";

type Overview = {
  organization: { name: string; plan: string; credits_balance: number; is_fixture: boolean };
  counts: { investigations: number; findings: number; reports: number; open_investigations: number };
  findings_by_type: { entity_type: string; count: number }[];
  sources: { id: string; status: string }[];
  recent_audit: { action: string; created_at: string }[];
};

export function OverviewScreen() {
  const { token, investigationId, can } = useWorkspace();
  const [data, setData] = useState<Overview | null>(null);
  const [graph, setGraph] = useState<GraphData>({ nodes: [], edges: [] });
  const [error, setError] = useState("");
  const [relation, setRelation] = useState("has_txt");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [evidence, setEvidence] = useState("");
  const [edgeError, setEdgeError] = useState("");

  async function load() {
    const overview = await api<Overview>("/api/v1/overview", {}, token);
    setData(overview);
    if (investigationId) {
      setGraph(await api<GraphData>(`/api/v1/investigations/${investigationId}/graph`, {}, token));
    } else {
      setGraph({ nodes: [], edges: [] });
    }
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, [token, investigationId]);

  async function addEdge(event: FormEvent) {
    event.preventDefault();
    setEdgeError("");
    try {
      await api(`/api/v1/investigations/${investigationId}/graph/edges`, {
        method: "POST",
        body: JSON.stringify({ from_node: from, to_node: to, relation, evidence, source_id: "analyst_record", confidence: 0.4 }),
      }, token);
      setEvidence("");
      await load();
    } catch (err) {
      setEdgeError(err instanceof Error ? err.message : "Link rejected");
    }
  }

  const max = Math.max(1, ...(data?.findings_by_type.map((item) => item.count) || [1]));
  const sourceCounts = (data?.sources || []).reduce<Record<string, number>>((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      <h1 className="page-title">Overview</h1>
      <p className="lede">Case activity for this organization. Counts come from stored searches, not from sample dashboards.</p>
      {error && <div className="error">{error}</div>}
      <div className="grid-4">
        <div className="stat"><b>{data?.counts.investigations ?? "—"}</b><span>Investigations</span></div>
        <div className="stat"><b>{data?.counts.open_investigations ?? "—"}</b><span>Open</span></div>
        <div className="stat"><b>{data?.counts.findings ?? "—"}</b><span>Findings</span></div>
        <div className="stat"><b>{data?.counts.reports ?? "—"}</b><span>Reports</span></div>
      </div>
      <div className="grid-2" style={{ marginTop: 14 }}>
        <section className="card">
          <h2>Findings by type</h2>
          {!data?.findings_by_type.length && <p className="muted">No findings yet.</p>}
          <svg className="chart" viewBox="0 0 420 180" role="img" aria-label="Findings by type">
            {data?.findings_by_type.map((item, index) => (
              <g key={item.entity_type} transform={`translate(0 ${index * 28})`}>
                <text x="0" y="16" fill="currentColor" fontSize="12">{item.entity_type}</text>
                <rect x="110" y="4" width={(item.count / max) * 250} height="14" rx="7" fill="#8b5cf6" />
                <text x="370" y="16" fill="currentColor" fontSize="12">{item.count}</text>
              </g>
            ))}
          </svg>
        </section>
        <section className="card">
          <h2>Source configuration</h2>
          <svg className="chart" viewBox="0 0 220 140" role="img" aria-label="Source status">
            {Object.entries(sourceCounts).map(([status, count], index) => (
              <g key={status} transform={`translate(0 ${index * 28})`}>
                <rect x="0" y="4" width={Math.max(8, count * 8)} height="14" rx="7" fill={status === "configured" ? "#22d3ee" : "#fbbf24"} />
                <text x="150" y="16" fill="currentColor" fontSize="12">{status} {count}</text>
              </g>
            ))}
          </svg>
          <h3>Recent audit</h3>
          <ul>{data?.recent_audit.map((item, index) => <li key={index}>{item.action}</li>)}</ul>
        </section>
      </div>
      <MfaCard />
      <section className="card">
        <h2>Investigation graph</h2>
        <GraphView graph={graph} />
        {can("investigate") && graph.nodes.length >= 2 && (
          <form onSubmit={addEdge} className="grid-2">
            <label>From
              <select value={from} onChange={(event) => setFrom(event.target.value)} required>
                <option value="">Select</option>
                {graph.nodes.map((node) => <option key={node.id} value={node.id}>{node.entity_type}: {node.label.slice(0, 48)}</option>)}
              </select>
            </label>
            <label>To
              <select value={to} onChange={(event) => setTo(event.target.value)} required>
                <option value="">Select</option>
                {graph.nodes.map((node) => <option key={node.id} value={node.id}>{node.entity_type}: {node.label.slice(0, 48)}</option>)}
              </select>
            </label>
            <label>Relation
              <select value={relation} onChange={(event) => setRelation(event.target.value)}>{RELATIONS.map((item) => <option key={item}>{item}</option>)}</select>
            </label>
            <label>Evidence<input value={evidence} onChange={(event) => setEvidence(event.target.value)} required minLength={3} /></label>
            <button className="btn" type="submit">Record evidence link</button>
            {edgeError && <div className="error">{edgeError}</div>}
          </form>
        )}
      </section>
    </div>
  );
}

function MfaCard() {
  const { token, me, refresh } = useWorkspace();
  const [secret, setSecret] = useState("");
  const [uri, setUri] = useState("");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("");
  if (me?.mfa_enabled) return <section className="card"><h2>Multi-factor authentication</h2><p>MFA is enabled for this account.</p></section>;
  return (
    <section className="card">
      <h2>Multi-factor authentication</h2>
      <p className="muted">Enrollment uses a real TOTP secret. It is stored encrypted and is not marked enabled until a code verifies.</p>
      <div className="cluster">
        <button className="btn secondary" type="button" onClick={async () => {
          const body = await api<{ secret: string; otpauth_uri: string }>("/api/v1/auth/mfa/setup", { method: "POST" }, token);
          setSecret(body.secret);
          setUri(body.otpauth_uri);
        }}>Start MFA setup</button>
        {secret && <label>Code<input value={code} onChange={(event) => setCode(event.target.value)} /></label>}
        {secret && <button className="btn" type="button" onClick={async () => {
          await api("/api/v1/auth/mfa/verify", { method: "POST", body: JSON.stringify({ code }) }, token);
          setMessage("MFA enabled.");
          await refresh();
        }}>Verify code</button>}
      </div>
      {uri && <p className="mono">{uri}</p>}
      {secret && <p className="mono">Secret: {secret}</p>}
      {message && <div className="note">{message}</div>}
    </section>
  );
}

type Analysis = {
  facts: { title: string; summary: string; source_id: string; confidence: number }[];
  hypotheses: { statement: string; confidence: number; kind: string }[];
  contradictions: { statement: string }[];
  timeline: { collected_at?: string; title: string; source_id: string }[];
  next_sources: string[];
  disclaimer: string;
  accuses_person: boolean;
};

export function AiScreen() {
  const { token, investigationId, refresh, can } = useWorkspace();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [title, setTitle] = useState("Investigation report");

  async function run() {
    setError("");
    try {
      setAnalysis(await api<Analysis>(`/api/v1/investigations/${investigationId}/ai`, { method: "POST" }, token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    }
  }

  async function createReport() {
    setError("");
    try {
      await api(`/api/v1/investigations/${investigationId}/reports`, { method: "POST", body: JSON.stringify({ title }) }, token);
      await refresh();
      setSaved("Report saved. Open Reports to read it.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the report");
    }
  }

  return (
    <div>
      <h1 className="page-title">AI Investigator</h1>
      <p className="lede">A local analyst separates verified observations from hypotheses. It does not accuse a person of a crime and it does not call an external model unless you add one later.</p>
      {!investigationId && <div className="note">Select or create an investigation first.</div>}
      <div className="cluster">
        <button className="btn" disabled={!investigationId || !can("report")} onClick={() => void run()}>Analyze case</button>
        <input aria-label="Report title" value={title} onChange={(event) => setTitle(event.target.value)} />
        <button className="btn secondary" disabled={!investigationId || !can("report")} onClick={() => void createReport()}>Save report</button>
      </div>
      {error && <div className="error">{error}</div>}
      {saved && <div className="note">{saved}</div>}
      {analysis && (
        <div className="card">
          <div className="banner">{analysis.disclaimer}</div>
          <h2>Verified observations</h2>
          <Findings findings={analysis.facts.map((fact) => ({ ...fact, value: fact.summary, normalized_value: fact.source_id, source_name: fact.source_id, verified: true, kind: "fact", entity_type: "fact" })) as Finding[]} />
          <h2>Hypotheses</h2>
          {analysis.hypotheses.length === 0 && <p className="muted">None generated.</p>}
          <ul>{analysis.hypotheses.map((item) => <li key={item.statement}>{item.statement}</li>)}</ul>
          <h2>Contradictions</h2>
          {analysis.contradictions.length === 0 && <p className="muted">No contradiction rule fired.</p>}
          <ul>{analysis.contradictions.map((item) => <li key={item.statement}>{item.statement}</li>)}</ul>
          <h2>Lawful next sources</h2>
          <ul>{analysis.next_sources.map((item) => <li key={item}>{item}</li>)}</ul>
          <h2>Timeline</h2>
          <ul>{analysis.timeline.map((item, index) => <li key={index}>{item.collected_at}: {item.title} ({item.source_id})</li>)}</ul>
        </div>
      )}
    </div>
  );
}

export function ReportsScreen() {
  const { token } = useWorkspace();
  const [rows, setRows] = useState<{ id: string; title: string; created_at: string }[]>([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ id: string; title: string; created_at: string }[]>("/api/v1/reports", {}, token).then(setRows).catch((err) => setError(err.message));
  }, [token]);

  async function open(id: string) {
    const report = await api<{ title: string; body_markdown: string }>(`/api/v1/reports/${id}`, {}, token);
    setBody(`# ${report.title}\n\n${report.body_markdown}`);
  }

  function download() {
    const blob = new Blob([body], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "infinityx-report.md";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <h1 className="page-title">Reports</h1>
      <p className="lede">Reports are generated from stored findings. They keep hypotheses separate from verified observations.</p>
      {error && <div className="error">{error}</div>}
      {!rows.length && <div className="note">No reports yet. Save one from AI Investigator.</div>}
      <div className="card">
        {rows.map((row) => (
          <div className="row" key={row.id} style={{ justifyContent: "space-between" }}>
            <span>{row.title}</span>
            <button className="btn secondary" onClick={() => void open(row.id)}>Open</button>
          </div>
        ))}
      </div>
      {body && (
        <section className="card">
          <button className="btn" onClick={download}>Download Markdown</button>
          <pre className="mono" style={{ whiteSpace: "pre-wrap" }}>{body}</pre>
        </section>
      )}
    </div>
  );
}
