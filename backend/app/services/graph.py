from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Finding as FindingRow
from app.models import GraphEdge, GraphNode
from app.services.policy import PolicyError, validate_edge
from app.services.results import Finding


def _node(db: Session, org_id: uuid.UUID, investigation_id: uuid.UUID, entity_type: str, value: str, confidence: float, source_id: str | None) -> GraphNode:
    normalized = value.strip()[:500]
    existing = (
        db.query(GraphNode)
        .filter(
            GraphNode.investigation_id == investigation_id,
            GraphNode.entity_type == entity_type,
            GraphNode.normalized_value == normalized,
        )
        .one_or_none()
    )
    if existing:
        if confidence > existing.confidence:
            existing.confidence = confidence
        return existing
    node = GraphNode(
        org_id=org_id,
        investigation_id=investigation_id,
        entity_type=entity_type,
        label=normalized,
        normalized_value=normalized,
        confidence=confidence,
        source_id=source_id,
    )
    db.add(node)
    db.flush()
    return node


def add_edge(
    db: Session,
    *,
    org_id: uuid.UUID,
    investigation_id: uuid.UUID,
    from_node: uuid.UUID,
    to_node: uuid.UUID,
    relation: str,
    evidence: str,
    source_id: str,
    confidence: float,
    collected_at: datetime,
    source_url: str | None = None,
) -> GraphEdge:
    score = validate_edge(relation, evidence, source_id, confidence)
    if from_node == to_node:
        raise PolicyError("An edge cannot link a node to itself")
    existing = (
        db.query(GraphEdge)
        .filter(
            GraphEdge.investigation_id == investigation_id,
            GraphEdge.from_node == from_node,
            GraphEdge.to_node == to_node,
            GraphEdge.relation == relation,
        )
        .one_or_none()
    )
    if existing:
        return existing
    edge = GraphEdge(
        org_id=org_id,
        investigation_id=investigation_id,
        from_node=from_node,
        to_node=to_node,
        relation=relation,
        evidence_summary=evidence.strip(),
        source_id=source_id,
        source_url=source_url,
        confidence=score,
        collected_at=collected_at,
    )
    db.add(edge)
    db.flush()
    return edge


def project_findings(
    db: Session,
    org_id: uuid.UUID,
    investigation_id: uuid.UUID,
    subject_type: str,
    subject_value: str,
    findings: list[Finding],
) -> None:
    if not subject_value:
        return
    subject = _node(db, org_id, investigation_id, subject_type, subject_value, 0.5, "local_normalizer")
    for finding in findings:
        for link in (finding.attributes or {}).get("links") or []:
            relation = link.get("relation") or ""
            evidence = link.get("evidence") or finding.summary
            target_value = str(link.get("target_value") or "").strip()
            target_type = str(link.get("target_type") or "host")
            if not target_value:
                continue
            try:
                target = _node(db, org_id, investigation_id, target_type, target_value, finding.confidence, finding.source_id)
                add_edge(
                    db,
                    org_id=org_id,
                    investigation_id=investigation_id,
                    from_node=subject.id,
                    to_node=target.id,
                    relation=relation,
                    evidence=evidence,
                    source_id=finding.source_id,
                    confidence=finding.confidence,
                    collected_at=finding.collected_at,
                    source_url=finding.source_url,
                )
            except PolicyError:
                continue


def replace_investigation(db: Session, finding: FindingRow, investigation_id: uuid.UUID) -> None:
    finding.investigation_id = investigation_id
