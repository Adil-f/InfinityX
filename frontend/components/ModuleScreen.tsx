"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Findings, NoticeList } from "@/components/Findings";
import { useWorkspace } from "@/components/Shell";
import { api, SearchResponse } from "@/lib/api";

const BASES = ["legitimate_interest", "consent", "legal_obligation", "contract", "public_task"];

export function ModuleScreen({
  module,
  title,
  lede,
  placeholder,
  phone = false,
  consent = false,
  forensics = false,
}: {
  module?: string;
  title: string;
  lede: string;
  placeholder: string;
  phone?: boolean;
  consent?: boolean;
  forensics?: boolean;
}) {
  const params = useSearchParams();
  const workspace = useWorkspace();
  const [query, setQuery] = useState("");
  const [text, setText] = useState("");
  const [region, setRegion] = useState("");
  const [purpose, setPurpose] = useState("Authorized security investigation");
  const [basis, setBasis] = useState("legitimate_interest");
  const [agreed, setAgreed] = useState(false);
  const [save, setSave] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);

  useEffect(() => {
    const initial = params.get("q");
    if (initial) setQuery(initial);
  }, [params]);

  useEffect(() => {
    document.title = `${title} · Infinity X`;
  }, [title]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setResult(null);
    if (!workspace.can("search")) {
      setError("Your role can review cases but cannot run searches.");
      return;
    }
    setLoading(true);
    try {
      const investigation_id = save && workspace.investigationId ? workspace.investigationId : null;
      if (forensics) {
        const body = await api<SearchResponse>("/api/v1/forensics", {
          method: "POST",
          body: JSON.stringify({ text, purpose, lawful_basis: basis, investigation_id }),
        }, workspace.token);
        setResult(body);
      } else {
        const body = await api<SearchResponse>("/api/v1/search", {
          method: "POST",
          body: JSON.stringify({
            query,
            module: module || null,
            region: region || null,
            purpose,
            lawful_basis: basis,
            consent: agreed,
            investigation_id,
          }),
        }, workspace.token);
        setResult(body);
      }
      await workspace.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function onFile(file: File) {
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    let binary = "";
    bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
    const content_base64 = btoa(binary);
    setLoading(true);
    setError("");
    try {
      const body = await api<SearchResponse>("/api/v1/forensics", {
        method: "POST",
        body: JSON.stringify({
          content_base64,
          filename: file.name,
          purpose,
          lawful_basis: basis,
          investigation_id: save && workspace.investigationId ? workspace.investigationId : null,
        }),
      }, workspace.token);
      setResult(body);
      await workspace.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hashing failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">{title}</h1>
      <p className="lede">{lede}</p>
      {!workspace.can("search") && <div className="note">Your role can review results but cannot run new searches.</div>}
      <form className="card" onSubmit={onSubmit}>
        {!forensics && <label>Query<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={placeholder} required /></label>}
        {forensics && <label>Text evidence<textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste text to hash locally" /></label>}
        {phone && (
          <label>Parsing hint
            <select value={region} onChange={(event) => setRegion(event.target.value)}>
              <option value="">International + required</option>
              <option value="PK">Pakistan</option>
              <option value="IT">Italy</option>
            </select>
          </label>
        )}
        <div className="grid-2" style={{ marginTop: 10 }}>
          <label>Purpose<input value={purpose} onChange={(event) => setPurpose(event.target.value)} required minLength={8} /></label>
          <label>Lawful basis
            <select value={basis} onChange={(event) => setBasis(event.target.value)}>{BASES.map((item) => <option key={item}>{item}</option>)}</select>
          </label>
        </div>
        <div className="checks" style={{ marginTop: 10 }}>
          <label className="check"><input type="checkbox" checked={save} onChange={(event) => setSave(event.target.checked)} /> Save into the selected investigation</label>
          {consent && <label className="check"><input type="checkbox" checked={agreed} onChange={(event) => setAgreed(event.target.checked)} required /> I confirm this format check is authorized. It does not query an identity registry.</label>}
        </div>
        <div className="cluster" style={{ marginTop: 12 }}>
          <button className="btn" disabled={loading || !workspace.can("search")}>{loading ? "Running…" : "Run"}</button>
          {forensics && <label className="btn secondary">Hash a file<input type="file" hidden onChange={(event) => { const file = event.target.files?.[0]; if (file) void onFile(file); }} /></label>}
        </div>
      </form>
      {error && <div className="error">{error}</div>}
      {result && (
        <section className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <strong>Status: {result.status}</strong>
            <span className="muted">Charged {result.credits_charged} · remaining {result.credits_remaining}</span>
          </div>
          {result.notes?.map((note) => <p key={note} className="muted">{note}</p>)}
          <NoticeList title="Unavailable sources" items={result.unavailable || []} tone="note" />
          <NoticeList title="Errors" items={result.errors || []} tone="error" />
          {result.status === "needs_disambiguation" && (
            <div className="cluster">
              <Link className="btn" href={`/phone?q=${encodeURIComponent(query)}`}>Open Phone</Link>
              <Link className="btn secondary" href={`/cnic?q=${encodeURIComponent(query)}`}>Open CNIC</Link>
            </div>
          )}
          {result.suggested_module && <p><Link href={`/${result.suggested_module}?q=${encodeURIComponent(query)}`}>Continue in {result.suggested_module}</Link></p>}
          {result.provider_response && (
            <div className="note">
              <strong>Authorized provider response</strong>
              <p>{result.provider_response.note} Stored at rest: {String(result.provider_response.stored_at_rest)}.</p>
              <pre className="mono">{JSON.stringify(result.provider_response.payload, null, 2)}</pre>
            </div>
          )}
          <Findings findings={result.findings || []} />
        </section>
      )}
    </div>
  );
}
