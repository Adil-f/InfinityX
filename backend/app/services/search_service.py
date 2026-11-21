from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AuditLog, ConsentRecord, CreditLedger, Finding as FindingRow
from app.models import Investigation, Organization, SearchJob
from app.security import LOCAL_MODULES, Principal, credit_cost, utcnow
from app.services.classify import classify_query
from app.services.graph import project_findings
from app.services.modules import run_query
from app.services.results import publishable

SUBJECT_TYPE = {
    "phone": "phone",
    "cnic": "cnic",
    "email": "email",
    "domain": "domain",
    "ip": "ip",
    "url": "domain",
    "username": "username",
    "social": "username",
    "threat": "indicator",
}


def _audit(db: Session, principal: Principal, action: str, resource_type: str | None, resource_id: str | None, ip: str | None, details: dict) -> None:
    db.add(
        AuditLog(
            org_id=principal.org_id,
            user_id=principal.actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip=ip,
            details=details,
        )
    )


def uses_keyed_vendor(query_type: str) -> bool:
    from app.config import settings

    if query_type in {"username", "social"}:
        return True
    if query_type == "email" and settings.hibp_api_key:
        return True
    if query_type in {"threat", "ip", "url"} and (settings.virustotal_api_key or settings.otx_api_key):
        return True
    return False


def _disabled(db: Session, org_id) -> set[str]:
    from app.models import ConnectorState

    rows = db.query(ConnectorState).filter(ConnectorState.org_id == org_id, ConnectorState.enabled.is_(False)).all()
    return {row.connector_id for row in rows}


def _load_investigation(db: Session, principal: Principal, investigation_id: uuid.UUID) -> Investigation:
    row = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id, Investigation.org_id == principal.org_id)
        .one_or_none()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return row


def execute_search(
    db: Session,
    principal: Principal,
    *,
    query: str,
    module: str | None,
    purpose: str,
    lawful_basis: str,
    investigation_id: uuid.UUID | None,
    region: str | None,
    client_ip: str | None,
) -> dict:
    if investigation_id and not principal.allows("investigate"):
        raise HTTPException(status_code=403, detail="Missing permission to attach results to an investigation")
    investigation = _load_investigation(db, principal, investigation_id) if investigation_id else None
    preview = classify_query(query, module if module and module != "universal" else None)
    expected_cost = 0 if preview["query_type"] in LOCAL_MODULES | {"ambiguous_numeric", "rejected"} else credit_cost(preview["query_type"])
    reserved = False
    org_locked = None
    if uses_keyed_vendor(preview["query_type"]):
        org_locked = db.query(Organization).filter(Organization.id == principal.org_id).with_for_update().one()
        if org_locked.credits_balance < 1:
            db.rollback()
            raise HTTPException(status_code=402, detail="Insufficient credits")
        org_locked.credits_balance -= 1
        reserved = True
        db.flush()
    else:
        org_preview = db.query(Organization).filter(Organization.id == principal.org_id).one()
        if expected_cost and org_preview.credits_balance < expected_cost:
            raise HTTPException(status_code=402, detail="Insufficient credits")
    disabled = _disabled(db, principal.org_id)
    result = run_query(
        query,
        module,
        region=region,
        purpose=purpose,
        case_id=str(investigation_id) if investigation_id else None,
        disabled=disabled,
    )
    if result.status in {"needs_disambiguation", "rejected"}:
        if reserved and org_locked is not None:
            org_locked.credits_balance += 1
        _audit(
            db,
            principal,
            "search.reject",
            "search",
            None,
            client_ip,
            {"query_type": result.query_type, "status": result.status},
        )
        db.commit()
        return _payload(None, result, 0, _credits(db, principal.org_id))

    findings, blocked = publishable(result.findings)
    if blocked:
        result.errors.append({
            "source_id": "local_normalizer",
            "source_name": "Local normalizer",
            "message": "A fixture result was blocked and was not returned.",
        })
    result.findings = findings
    cost = 1 if result.external_attempted else 0
    if reserved and org_locked is not None:
        org = org_locked
        if cost == 0:
            org.credits_balance += 1
    else:
        org = db.query(Organization).filter(Organization.id == principal.org_id).with_for_update().one()
        if cost and org.credits_balance < cost:
            db.rollback()
            raise HTTPException(status_code=402, detail="Insufficient credits")
    stored_query = result.normalized_query if result.query_type == "cnic" else query.strip()[:512]
    audit_details = {"query_type": result.query_type, "module": module or result.query_type, "external": result.external_attempted}
    if result.query_type == "cnic":
        audit_details["identifier_stored"] = "redacted"
    else:
        audit_details["query"] = stored_query[:120]
    job = SearchJob(
        org_id=principal.org_id,
        investigation_id=investigation.id if investigation else None,
        user_id=principal.actor_id,
        query=stored_query,
        normalized_query=result.normalized_query or stored_query,
        query_type=result.query_type,
        module=module or result.query_type,
        status="completed",
        credit_cost=cost,
        external_attempted=result.external_attempted,
        result_meta={
            "unavailable": result.unavailable,
            "errors": result.errors,
            "notes": result.notes,
        },
    )
    db.add(job)
    db.flush()
    if cost and not reserved:
        org.credits_balance -= cost
    if cost:
        db.add(CreditLedger(org_id=org.id, delta=-cost, reason="search", search_job_id=job.id))
    rows = []
    for finding in findings:
        row = FindingRow(
            org_id=principal.org_id,
            investigation_id=investigation.id if investigation else None,
            search_job_id=job.id,
            entity_type=finding.entity_type,
            value=finding.value,
            normalized_value=finding.normalized_value,
            title=finding.title,
            summary=finding.summary,
            source_id=finding.source_id,
            source_name=finding.source_name,
            source_url=finding.source_url,
            collected_at=finding.collected_at,
            confidence=finding.confidence,
            verified=finding.verified,
            kind=finding.kind,
            attributes=finding.attributes,
            is_fixture=False,
        )
        db.add(row)
        rows.append(row)
    if investigation:
        subject_type = SUBJECT_TYPE.get(result.query_type, result.query_type)
        project_findings(db, principal.org_id, investigation.id, subject_type, result.normalized_query, findings)
    text_version = "cnic-format-v1" if result.query_type == "cnic" else "search-v1"
    if principal.actor_id:
        db.add(
            ConsentRecord(
                org_id=principal.org_id,
                user_id=principal.actor_id,
                purpose=purpose.strip(),
                lawful_basis=lawful_basis,
                subject_type=result.query_type,
                text_version=text_version,
            )
        )
    _audit(db, principal, "cnic.validate" if result.query_type == "cnic" else "search.run", "search_job", str(job.id), client_ip, audit_details)
    db.commit()
    return _payload(job.id, result, cost, org.credits_balance)


def attach_job(db: Session, principal: Principal, job_id: uuid.UUID, investigation_id: uuid.UUID) -> dict:
    job = db.query(SearchJob).filter(SearchJob.id == job_id, SearchJob.org_id == principal.org_id).one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Search job not found")
    investigation = _load_investigation(db, principal, investigation_id)
    job.investigation_id = investigation.id
    findings = db.query(FindingRow).filter(FindingRow.search_job_id == job.id).all()
    from app.services.results import Finding

    projected = []
    for row in findings:
        row.investigation_id = investigation.id
        projected.append(
            Finding(
                entity_type=row.entity_type,
                value=row.value,
                normalized_value=row.normalized_value,
                title=row.title,
                summary=row.summary,
                source_id=row.source_id,
                source_name=row.source_name,
                confidence=row.confidence,
                verified=row.verified,
                kind=row.kind,
                source_url=row.source_url,
                collected_at=row.collected_at,
                attributes=row.attributes or {},
            )
        )
    project_findings(db, principal.org_id, investigation.id, SUBJECT_TYPE.get(job.query_type, job.query_type), job.normalized_query, projected)
    _audit(db, principal, "search.attach", "search_job", str(job.id), None, {"investigation_id": str(investigation.id)})
    db.commit()
    return {"job_id": str(job.id), "investigation_id": str(investigation.id), "findings": len(findings)}


def _credits(db: Session, org_id: uuid.UUID) -> int:
    org = db.query(Organization).filter(Organization.id == org_id).one()
    return org.credits_balance


def _payload(job_id, result, cost: int, remaining: int) -> dict:
    body = {
        "job_id": str(job_id) if job_id else None,
        "query_type": result.query_type,
        "normalized_query": result.normalized_query,
        "status": result.status,
        "credits_charged": cost,
        "credits_remaining": remaining,
        "findings": [finding.as_dict() for finding in result.findings],
        "unavailable": result.unavailable,
        "errors": result.errors,
        "notes": result.notes,
        "suggested_module": result.suggested_module,
        "options": ["phone", "cnic"] if result.status == "needs_disambiguation" else [],
    }
    if result.transient.get("provider_response"):
        body["provider_response"] = result.transient["provider_response"]
    return body


def apply_retention(db: Session, org_id: uuid.UUID) -> dict:
    now = utcnow()
    org = db.query(Organization).filter(Organization.id == org_id).one()
    expired = (
        db.query(Investigation)
        .filter(Investigation.org_id == org_id, Investigation.retention_until.is_not(None), Investigation.retention_until < now)
        .all()
    )
    removed_findings = 0
    for investigation in expired:
        removed_findings += db.query(FindingRow).filter(FindingRow.investigation_id == investigation.id).delete(synchronize_session=False)
        investigation.status = "expired"
    cutoff = now - timedelta(days=org.retention_days)
    removed_jobs = (
        db.query(SearchJob)
        .filter(SearchJob.org_id == org_id, SearchJob.investigation_id.is_(None), SearchJob.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"expired_investigations": len(expired), "removed_findings": removed_findings, "removed_unassigned_jobs": removed_jobs}
