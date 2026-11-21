from __future__ import annotations

import base64
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require
from app.models import Organization
from app.security import LAWFUL_BASES, Principal, validate_purpose
from app.services.forensics import hash_evidence
from app.services.ratelimit import allow, limit_for
from app.services.search_service import attach_job, execute_search

router = APIRouter(prefix="/api/v1", tags=["search"])


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    module: str | None = None
    region: str | None = None
    purpose: str
    lawful_basis: str
    investigation_id: uuid.UUID | None = None
    consent: bool = False


class AttachIn(BaseModel):
    investigation_id: uuid.UUID


class ForensicsIn(BaseModel):
    text: str | None = None
    content_base64: str | None = None
    filename: str | None = None
    purpose: str
    lawful_basis: str
    investigation_id: uuid.UUID | None = None


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _guard(body_purpose: str, lawful_basis: str, principal: Principal, db: Session) -> Organization:
    problem = validate_purpose(body_purpose, lawful_basis)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    if lawful_basis not in LAWFUL_BASES:
        raise HTTPException(status_code=422, detail="Unknown lawful basis")
    org = db.query(Organization).filter(Organization.id == principal.org_id).one()
    identity = str(principal.user_id or principal.api_key_id)
    if not allow(f"search:{identity}", limit_for(org.plan, "search")):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return org


@router.post("/search")
def search(body: SearchIn, request: Request, principal: Principal = Depends(require("search")), db: Session = Depends(get_db)):
    _guard(body.purpose, body.lawful_basis, principal, db)
    module = body.module
    if module == "cnic" or (module in {None, "universal"} and __import__("app.services.classify", fromlist=["classify_query"]).classify_query(body.query, None)["query_type"] == "cnic"):
        if not body.consent:
            raise HTTPException(status_code=422, detail="CNIC checks require an explicit consent confirmation. No identity registry was queried.")
    if module == "forensics":
        raise HTTPException(status_code=422, detail="Use the forensics endpoint with file content.")
    return execute_search(
        db,
        principal,
        query=body.query,
        module=None if module in {None, "universal", "auto"} else module,
        purpose=body.purpose,
        lawful_basis=body.lawful_basis,
        investigation_id=body.investigation_id,
        region=body.region,
        client_ip=_ip(request),
    )


@router.post("/search-jobs/{job_id}/attach")
def attach(job_id: uuid.UUID, body: AttachIn, principal: Principal = Depends(require("investigate")), db: Session = Depends(get_db)):
    return attach_job(db, principal, job_id, body.investigation_id)


@router.post("/forensics")
def forensics(body: ForensicsIn, request: Request, principal: Principal = Depends(require("search")), db: Session = Depends(get_db)):
    _guard(body.purpose, body.lawful_basis, principal, db)
    if body.content_base64:
        try:
            content = base64.b64decode(body.content_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="content_base64 is not valid base64") from exc
    elif body.text is not None:
        content = body.text.encode("utf-8")
    else:
        raise HTTPException(status_code=422, detail="Provide text or content_base64")
    hashed = hash_evidence(content, body.filename)
    if hashed.status == "rejected":
        raise HTTPException(status_code=422, detail=hashed.errors[0]["message"] if hashed.errors else "Could not hash content")
    from app.services.results import publishable
    from app.models import AuditLog, ConsentRecord, Finding as FindingRow, SearchJob

    findings, blocked = publishable(hashed.findings)
    job = SearchJob(
        org_id=principal.org_id,
        investigation_id=body.investigation_id,
        user_id=principal.actor_id,
        query=hashed.normalized_query,
        normalized_query=hashed.normalized_query,
        query_type="forensics",
        module="forensics",
        status="completed",
        credit_cost=0,
        external_attempted=False,
        result_meta={"notes": hashed.notes, "errors": hashed.errors, "unavailable": [], "blocked_fixture": blocked},
    )
    if body.investigation_id:
        from app.models import Investigation

        investigation = db.query(Investigation).filter(Investigation.id == body.investigation_id, Investigation.org_id == principal.org_id).one_or_none()
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        if not principal.allows("investigate"):
            raise HTTPException(status_code=403, detail="Missing permission to attach results to an investigation")
    db.add(job)
    db.flush()
    for finding in findings:
        db.add(
            FindingRow(
                org_id=principal.org_id,
                investigation_id=body.investigation_id,
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
        )
    if principal.actor_id:
        db.add(ConsentRecord(org_id=principal.org_id, user_id=principal.actor_id, purpose=body.purpose.strip(), lawful_basis=body.lawful_basis, subject_type="forensics", text_version="forensics-v1"))
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.actor_id, action="forensics.hash", resource_type="search_job", resource_id=str(job.id), ip=_ip(request), details={"bytes": len(content), "content_stored": False}))
    if body.investigation_id:
        from app.services.graph import project_findings

        project_findings(db, principal.org_id, body.investigation_id, "hash", hashed.normalized_query, findings)
    org = db.query(Organization).filter(Organization.id == principal.org_id).one()
    db.commit()
    return {
        "job_id": str(job.id),
        "query_type": "forensics",
        "normalized_query": hashed.normalized_query,
        "status": "completed",
        "credits_charged": 0,
        "credits_remaining": org.credits_balance,
        "findings": [finding.as_dict() for finding in findings],
        "unavailable": [],
        "errors": hashed.errors,
        "notes": hashed.notes,
    }
