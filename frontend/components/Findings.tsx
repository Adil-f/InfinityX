"use client";

import { Finding } from "@/lib/api";

export function Findings({ findings }: { findings: Finding[] }) {
  if (!findings.length) return <p className="muted">No findings were returned.</p>;
  return (
    <div>
      {findings.map((finding, index) => (
        <article className="finding" key={`${finding.source_id}-${finding.title}-${index}`}>
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3>{finding.title}</h3>
            <span className={`badge ${finding.kind}`}>{finding.verified ? "verified fact" : "unverified reference"}</span>
          </div>
          <p>{finding.summary}</p>
          <div className="row">
            <span className="meter" aria-label={`confidence ${Math.round(finding.confidence * 100)} percent`}><span style={{ width: `${Math.round(finding.confidence * 100)}%` }} /></span>
            <span className="muted">{Math.round(finding.confidence * 100)}% · {finding.source_name}</span>
            {finding.collected_at && <span className="muted">{new Date(finding.collected_at).toLocaleString()}</span>}
          </div>
          <div className="mono">{finding.value}</div>
          {finding.source_url && <a href={finding.source_url} target="_blank" rel="noreferrer">{finding.source_url}</a>}
        </article>
      ))}
    </div>
  );
}

export function NoticeList({ title, items, tone }: { title: string; items: { message: string; source_id?: string; required_env?: string[] }[]; tone: string }) {
  if (!items.length) return null;
  return (
    <div className={tone === "error" ? "error" : "note"}>
      <strong>{title}</strong>
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item.source_id ? `${item.source_id}: ` : ""}{item.message}{item.required_env?.length ? ` (${item.required_env.join(", ")})` : ""}</li>
        ))}
      </ul>
    </div>
  );
}
