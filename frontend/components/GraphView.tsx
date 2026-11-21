"use client";

import { useState } from "react";

type Node = { id: string; entity_type: string; label: string; confidence: number; source_id?: string | null };
type Edge = { id: string; from_node: string; to_node: string; relation: string; evidence: string; source_id: string; confidence: number; analyst_asserted: boolean };
export type GraphData = { nodes: Node[]; edges: Edge[] };

export function GraphView({ graph }: { graph: GraphData }) {
  const [selected, setSelected] = useState<string>("");
  if (!graph.nodes.length) {
    return <p className="muted">No evidence nodes yet. Run a search with this investigation selected. The graph does not infer that two records belong to the same person.</p>;
  }
  const radius = graph.nodes.length === 1 ? 0 : 150;
  const placed = graph.nodes.map((node, index) => {
    const angle = (Math.PI * 2 * index) / graph.nodes.length - Math.PI / 2;
    return { ...node, x: 300 + radius * Math.cos(angle), y: 200 + radius * Math.sin(angle) };
  });
  const byId = Object.fromEntries(placed.map((node) => [node.id, node]));
  const current = placed.find((node) => node.id === selected);
  return (
    <div className="graph-wrap">
      <svg className="graph" viewBox="0 0 600 400" role="img" aria-label="Investigation graph">
        {graph.edges.map((edge) => {
          const from = byId[edge.from_node];
          const to = byId[edge.to_node];
          if (!from || !to) return null;
          return (
            <g key={edge.id}>
              <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#22d3ee" strokeWidth="1.4" />
              <text x={(from.x + to.x) / 2} y={(from.y + to.y) / 2} fill="#93a0bd" fontSize="10">{edge.relation}</text>
            </g>
          );
        })}
        {placed.map((node) => (
          <g key={node.id} onClick={() => setSelected(node.id)} style={{ cursor: "pointer" }}>
            <circle cx={node.x} cy={node.y} r="22" fill="#111827" stroke={selected === node.id ? "#22d3ee" : "#8b5cf6"} strokeWidth="2" />
            <text x={node.x} y={node.y + 36} textAnchor="middle" fill="currentColor" fontSize="11">{node.entity_type}</text>
          </g>
        ))}
      </svg>
      {current && (
        <div className="note">
          <strong>{current.entity_type}</strong>
          <div className="mono">{current.label}</div>
          <div className="muted">Confidence {Math.round(current.confidence * 100)}% · source {current.source_id || "n/a"}</div>
        </div>
      )}
    </div>
  );
}

export const RELATIONS = ["has_domain", "has_mx", "has_ns", "has_spf", "has_dmarc", "has_dkim", "resolves_to", "ptr", "has_asn", "has_registrar", "certificate_names", "public_account", "has_txt"];
