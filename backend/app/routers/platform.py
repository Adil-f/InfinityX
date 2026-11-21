from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.connectors.catalog import CONNECTORS, configuration_status, connector_by_id, missing_env
from app.db import get_db
from app.deps import require, require_session
from app.models import (
    ApiKey,
    AuditLog,
    ConsentRecord,
    CreditLedger,
    Finding as FindingRow,
    GraphEdge,
    GraphNode,
    Investigation,
    Organization,
    Report,
    SearchJob,
    Team,
    TeamMember,
    User,
    ConnectorState,
)
from app.security import API_SCOPE_PERMISSIONS, PLANS, Principal, hash_api_key, hash_password, permissions_for, utcnow, validate_password, validate_purpose
from app.services.ai import analyze
from app.services.graph import add_edge
from app.services.health import probe_connector
from app.services.policy import PolicyError
from app.services.reports import render_report
from app.services.search_service import apply_retention

router = APIRouter(prefix="/api/v1", tags=["platform"])


class InvestigationIn(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    purpose: str
    lawful_basis: str
    classification: str = "internal"


class EdgeIn(BaseModel):
    from_node: uuid.UUID
    to_node: uuid.UUID
    relation: str
    evidence: str
    source_id: str = "analyst_record"
    confidence: float = 0.4


class ReportIn(BaseModel):
    title: str = Field(min_length=3, max_length=160)


class KeyIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    scopes: list[str] = Field(default_factory=lambda: ["search", "read"])


class PlanIn(BaseModel):
    plan: str


class UserIn(BaseModel):
    email: str
    full_name: str
    role: str
    password: str


class UserPatch(BaseModel):
    role: str | None = None
    status: str | None = None


class TeamIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class MemberIn(BaseModel):
    user_id: uuid.UUID


class RetentionIn(BaseModel):
    days: int = Field(ge=7, le=3650)


class SourcePatch(BaseModel):
    enabled: bool


def _org(db: Session, principal: Principal) -> Organization:
    return db.query(Organization).filter(Organization.id == principal.org_id).one()


def _investigation(db: Session, principal: Principal, investigation_id: uuid.UUID) -> Investigation:
    row = db.query(Investigation).filter(Investigation.id == investigation_id, Investigation.org_id == principal.org_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return row


def _finding_dict(row: FindingRow) -> dict:
    return {
        "id": str(row.id),
        "entity_type": row.entity_type,
        "value": row.value,
        "normalized_value": row.normalized_value,
        "title": row.title,
        "summary": row.summary,
        "source_id": row.source_id,
        "source_name": row.source_name,
        "source_url": row.source_url,
        "collected_at": row.collected_at.isoformat() if row.collected_at else None,
        "confidence": row.confidence,
        "verified": row.verified,
        "kind": row.kind,
        "attributes": row.attributes or {},
        "is_fixture": False,
    }


@router.get("/overview")
def overview(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    org = _org(db, principal)
    by_type = (
        db.query(FindingRow.entity_type, func.count())
        .filter(FindingRow.org_id == principal.org_id)
        .group_by(FindingRow.entity_type)
        .all()
    )
    audits = (
        db.query(AuditLog)
        .filter(AuditLog.org_id == principal.org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(8)
        .all()
    )
    sources = []
    states = {row.connector_id: row for row in db.query(ConnectorState).filter(ConnectorState.org_id == principal.org_id).all()}
    for spec in CONNECTORS:
        state = states.get(spec["id"])
        enabled = True if state is None else state.enabled
        sources.append({"id": spec["id"], "status": configuration_status(spec, settings, enabled)})
    return {
        "organization": {"name": org.name, "plan": org.plan, "credits_balance": org.credits_balance, "is_fixture": org.is_fixture},
        "counts": {
            "investigations": db.query(Investigation).filter(Investigation.org_id == principal.org_id).count(),
            "findings": db.query(FindingRow).filter(FindingRow.org_id == principal.org_id).count(),
            "reports": db.query(Report).filter(Report.org_id == principal.org_id).count(),
            "open_investigations": db.query(Investigation).filter(Investigation.org_id == principal.org_id, Investigation.status == "open").count(),
        },
        "findings_by_type": [{"entity_type": name, "count": count} for name, count in by_type],
        "sources": sources,
        "recent_audit": [
            {"action": row.action, "created_at": row.created_at.isoformat(), "resource_type": row.resource_type}
            for row in audits
        ],
    }


@router.get("/investigations")
def list_investigations(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    rows = db.query(Investigation).filter(Investigation.org_id == principal.org_id).order_by(Investigation.created_at.desc()).all()
    return [
        {
            "id": str(row.id),
            "title": row.title,
            "status": row.status,
            "purpose": row.purpose,
            "lawful_basis": row.lawful_basis,
            "classification": row.classification,
            "retention_until": row.retention_until.isoformat() if row.retention_until else None,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.post("/investigations")
def create_investigation(body: InvestigationIn, principal: Principal = Depends(require("investigate")), db: Session = Depends(get_db)):
    problem = validate_purpose(body.purpose, body.lawful_basis)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    org = _org(db, principal)
    row = Investigation(
        org_id=principal.org_id,
        title=body.title.strip(),
        purpose=body.purpose.strip(),
        lawful_basis=body.lawful_basis,
        classification=body.classification if body.classification in {"internal", "confidential", "restricted"} else "internal",
        created_by=principal.user_id,
        retention_until=utcnow() + timedelta(days=org.retention_days),
    )
    db.add(row)
    db.flush()
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="investigation.create", resource_type="investigation", resource_id=str(row.id), details={"title": row.title}))
    db.commit()
    return {"id": str(row.id), "title": row.title, "status": row.status}


@router.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: uuid.UUID, principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    row = _investigation(db, principal, investigation_id)
    findings = db.query(FindingRow).filter(FindingRow.investigation_id == row.id).order_by(FindingRow.collected_at.asc()).all()
    return {
        "id": str(row.id),
        "title": row.title,
        "status": row.status,
        "purpose": row.purpose,
        "lawful_basis": row.lawful_basis,
        "classification": row.classification,
        "retention_until": row.retention_until.isoformat() if row.retention_until else None,
        "findings": [_finding_dict(item) for item in findings],
    }


@router.delete("/investigations/{investigation_id}")
def delete_investigation(investigation_id: uuid.UUID, principal: Principal = Depends(require("investigate")), db: Session = Depends(get_db)):
    row = _investigation(db, principal, investigation_id)
    db.delete(row)
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="investigation.delete", resource_type="investigation", resource_id=str(investigation_id), details={}))
    db.commit()
    return {"deleted": True}


@router.get("/investigations/{investigation_id}/graph")
def get_graph(investigation_id: uuid.UUID, principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    row = _investigation(db, principal, investigation_id)
    nodes = db.query(GraphNode).filter(GraphNode.investigation_id == row.id).all()
    edges = db.query(GraphEdge).filter(GraphEdge.investigation_id == row.id).all()
    return {
        "investigation_id": str(row.id),
        "nodes": [
            {
                "id": str(node.id),
                "entity_type": node.entity_type,
                "label": node.label,
                "normalized_value": node.normalized_value,
                "confidence": node.confidence,
                "source_id": node.source_id,
            }
            for node in nodes
        ],
        "edges": [
            {
                "id": str(edge.id),
                "from_node": str(edge.from_node),
                "to_node": str(edge.to_node),
                "relation": edge.relation,
                "evidence": edge.evidence_summary,
                "source_id": edge.source_id,
                "confidence": edge.confidence,
                "collected_at": edge.collected_at.isoformat(),
                "analyst_asserted": edge.source_id == "analyst_record",
            }
            for edge in edges
        ],
    }


@router.post("/investigations/{investigation_id}/graph/edges")
def create_edge(investigation_id: uuid.UUID, body: EdgeIn, principal: Principal = Depends(require("investigate")), db: Session = Depends(get_db)):
    row = _investigation(db, principal, investigation_id)
    left = db.query(GraphNode).filter(GraphNode.id == body.from_node, GraphNode.investigation_id == row.id).one_or_none()
    right = db.query(GraphNode).filter(GraphNode.id == body.to_node, GraphNode.investigation_id == row.id).one_or_none()
    if not left or not right:
        raise HTTPException(status_code=404, detail="Graph node not found")
    try:
        edge = add_edge(
            db,
            org_id=principal.org_id,
            investigation_id=row.id,
            from_node=left.id,
            to_node=right.id,
            relation=body.relation,
            evidence=body.evidence,
            source_id="analyst_record",
            confidence=body.confidence,
            collected_at=utcnow(),
        )
    except PolicyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.actor_id, action="graph.edge", resource_type="graph_edge", resource_id=str(edge.id), details={"relation": body.relation, "source_id": edge.source_id}))
    db.commit()
    return {"id": str(edge.id), "relation": edge.relation, "confidence": edge.confidence, "analyst_asserted": edge.source_id == "analyst_record"}


@router.post("/investigations/{investigation_id}/ai")
def ai_analyze(investigation_id: uuid.UUID, principal: Principal = Depends(require("report")), db: Session = Depends(get_db)):
    row = _investigation(db, principal, investigation_id)
    findings = [_finding_dict(item) for item in db.query(FindingRow).filter(FindingRow.investigation_id == row.id).all()]
    unavailable = []
    for job in db.query(SearchJob).filter(SearchJob.investigation_id == row.id).all():
        unavailable.extend((job.result_meta or {}).get("unavailable") or [])
    analysis = analyze(findings, unavailable)
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="ai.analyze", resource_type="investigation", resource_id=str(row.id), details={"facts": len(analysis["facts"])}))
    db.commit()
    return analysis


@router.get("/reports")
def list_reports(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    rows = db.query(Report).filter(Report.org_id == principal.org_id).order_by(Report.created_at.desc()).all()
    return [
        {"id": str(row.id), "title": row.title, "investigation_id": str(row.investigation_id), "created_at": row.created_at.isoformat()}
        for row in rows
    ]


@router.post("/investigations/{investigation_id}/reports")
def create_report(investigation_id: uuid.UUID, body: ReportIn, principal: Principal = Depends(require("report")), db: Session = Depends(get_db)):
    row = _investigation(db, principal, investigation_id)
    findings = [_finding_dict(item) for item in db.query(FindingRow).filter(FindingRow.investigation_id == row.id).all()]
    unavailable = []
    for job in db.query(SearchJob).filter(SearchJob.investigation_id == row.id).all():
        unavailable.extend((job.result_meta or {}).get("unavailable") or [])
    markdown = render_report(title=body.title.strip(), purpose=row.purpose, lawful_basis=row.lawful_basis, findings=findings, unavailable=unavailable)
    report = Report(org_id=principal.org_id, investigation_id=row.id, title=body.title.strip(), body_markdown=markdown, created_by=principal.user_id)
    db.add(report)
    db.flush()
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="report.create", resource_type="report", resource_id=str(report.id), details={}))
    db.commit()
    return {"id": str(report.id), "title": report.title, "body_markdown": report.body_markdown}


@router.get("/reports/{report_id}")
def get_report(report_id: uuid.UUID, principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    row = db.query(Report).filter(Report.id == report_id, Report.org_id == principal.org_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"id": str(row.id), "title": row.title, "investigation_id": str(row.investigation_id), "body_markdown": row.body_markdown, "created_at": row.created_at.isoformat()}


@router.get("/sources")
def list_sources(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    states = {row.connector_id: row for row in db.query(ConnectorState).filter(ConnectorState.org_id == principal.org_id).all()}
    payload = []
    for spec in CONNECTORS:
        state = states.get(spec["id"])
        enabled = True if state is None else state.enabled
        payload.append({
            "id": spec["id"],
            "name": spec["name"],
            "category": spec["category"],
            "description": spec["description"],
            "required_env": spec.get("required_env") or [],
            "optional_env": spec.get("optional_env") or [],
            "missing_env": missing_env(spec, settings),
            "enabled": enabled,
            "configuration": configuration_status(spec, settings, enabled),
            "last_health": None if state is None else state.last_health,
            "last_checked_at": None if state is None or state.last_checked_at is None else state.last_checked_at.isoformat(),
            "last_error": None if state is None else state.last_error,
        })
    return payload


@router.post("/sources/{source_id}/health")
def source_health(source_id: str, principal: Principal = Depends(require("sources")), db: Session = Depends(get_db)):
    spec = connector_by_id(source_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Unknown source")
    state = db.query(ConnectorState).filter(ConnectorState.org_id == principal.org_id, ConnectorState.connector_id == source_id).one_or_none()
    if state and not state.enabled:
        result = {"status": "disabled", "detail": "Disabled by an administrator. The source was not queried."}
    elif source_id in {"hibp", "virustotal", "otx", "stripe", "authorized_identity"}:
        missing = missing_env(spec, settings)
        if missing:
            result = {"status": "unavailable", "detail": "Missing configuration. Shared vendor credentials are not probed from organization health checks.", "required_env": missing}
        else:
            result = {"status": "not_probed", "detail": "Shared vendor credentials are not used by organization health checks."}
    else:
        result = probe_connector(source_id)
    if state is None:
        state = ConnectorState(org_id=principal.org_id, connector_id=source_id, enabled=True)
        db.add(state)
    state.last_health = result["status"]
    state.last_checked_at = utcnow()
    state.last_error = None if result["status"] in {"ok", "unavailable", "disabled", "not_probed"} else result.get("detail")
    db.commit()
    return {"id": source_id, **result}


@router.patch("/sources/{source_id}")
def patch_source(source_id: str, body: SourcePatch, principal: Principal = Depends(require("sources")), db: Session = Depends(get_db)):
    if not connector_by_id(source_id):
        raise HTTPException(status_code=404, detail="Unknown source")
    state = db.query(ConnectorState).filter(ConnectorState.org_id == principal.org_id, ConnectorState.connector_id == source_id).one_or_none()
    if state is None:
        state = ConnectorState(org_id=principal.org_id, connector_id=source_id)
        db.add(state)
    state.enabled = body.enabled
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="source.toggle", resource_type="source", resource_id=source_id, details={"enabled": body.enabled}))
    db.commit()
    return {"id": source_id, "enabled": state.enabled}


@router.get("/api-keys")
def list_keys(principal: Principal = Depends(require("apikeys")), db: Session = Depends(get_db)):
    rows = db.query(ApiKey).filter(ApiKey.org_id == principal.org_id).order_by(ApiKey.created_at.desc()).all()
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "prefix": row.key_prefix,
            "scopes": row.scopes.split(","),
            "revoked": row.revoked_at is not None,
            "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.post("/api-keys")
def create_key(body: KeyIn, principal: Principal = Depends(require("apikeys")), db: Session = Depends(get_db)):
    allowed = {"search", "read"}
    creator_permissions = permissions_for(principal.role, principal.auth, principal.scopes)
    scopes = []
    for scope in body.scopes:
        if scope not in allowed:
            raise HTTPException(status_code=422, detail="Choose at least one of: search, read")
        if not API_SCOPE_PERMISSIONS[scope] <= creator_permissions:
            raise HTTPException(status_code=422, detail="API key scopes cannot exceed your permissions")
        scopes.append(scope)
    if not scopes:
        raise HTTPException(status_code=422, detail="Choose at least one of: search, read")
    token = "ix_" + secrets.token_urlsafe(32)
    row = ApiKey(
        org_id=principal.org_id,
        name=body.name.strip(),
        key_prefix=token[:11],
        key_hash=hash_api_key(token),
        scopes=",".join(scopes),
        created_by=principal.user_id,
    )
    db.add(row)
    db.flush()
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="apikey.create", resource_type="api_key", resource_id=str(row.id), details={"name": row.name}))
    db.commit()
    return {"id": str(row.id), "token": token, "prefix": row.key_prefix, "scopes": scopes, "shown_once": True}


@router.delete("/api-keys/{key_id}")
def revoke_key(key_id: uuid.UUID, principal: Principal = Depends(require("apikeys")), db: Session = Depends(get_db)):
    row = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.org_id == principal.org_id).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    row.revoked_at = utcnow()
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="apikey.revoke", resource_type="api_key", resource_id=str(row.id), details={}))
    db.commit()
    return {"revoked": True}


@router.get("/billing")
def billing(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    org = _org(db, principal)
    ledger = db.query(CreditLedger).filter(CreditLedger.org_id == org.id).order_by(CreditLedger.created_at.desc()).limit(20).all()
    return {
        "plan": org.plan,
        "credits_balance": org.credits_balance,
        "stripe_configured": bool(settings.stripe_secret_key),
        "charged": False,
        "plans": [
            {
                "id": key,
                "label": value["label"],
                "credits": value["credits"],
                "searches_per_minute": value["searches_per_minute"],
                "list_price_eur": value["list_price_eur"],
                "note": "List price only. No charge is created unless a configured Stripe Checkout session is completed.",
            }
            for key, value in PLANS.items()
        ],
        "ledger": [{"delta": row.delta, "reason": row.reason, "created_at": row.created_at.isoformat()} for row in ledger],
    }


@router.post("/billing/checkout")
def checkout(body: PlanIn, principal: Principal = Depends(require("billing")), db: Session = Depends(get_db)):
    if body.plan not in {"pro", "enterprise"}:
        raise HTTPException(status_code=422, detail="Checkout is available for pro or enterprise")
    price = settings.stripe_price_pro if body.plan == "pro" else settings.stripe_price_enterprise
    required = ["STRIPE_SECRET_KEY", "STRIPE_PRICE_PRO" if body.plan == "pro" else "STRIPE_PRICE_ENTERPRISE"]
    if not settings.stripe_secret_key or not price:
        return {
            "status": "unavailable",
            "charged": False,
            "required_env": required,
            "message": "Stripe is not configured. No charge was created.",
        }
    import stripe

    stripe.api_key = settings.stripe_secret_key
    org = _org(db, principal)
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price, "quantity": 1}],
            success_url=f"{settings.public_app_url}/billing?checkout=success",
            cancel_url=f"{settings.public_app_url}/billing?checkout=cancel",
            metadata={"org_id": str(org.id), "plan": body.plan},
            customer_email=principal.email,
        )
    except Exception as exc:
        return {"status": "error", "charged": False, "message": f"Stripe rejected the checkout request: {exc}"[:300]}
    return {"status": "ok", "charged": False, "url": session.url, "message": "Redirect the browser to Stripe. This call does not capture a payment."}


@router.post("/billing/plan")
def set_plan(body: PlanIn, principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    if body.plan not in PLANS:
        raise HTTPException(status_code=422, detail="Unknown plan")
    org = _org(db, principal)
    org.plan = body.plan
    org.credits_balance = PLANS[body.plan]["credits"]
    db.add(CreditLedger(org_id=org.id, delta=PLANS[body.plan]["credits"], reason="administrative plan allowance (no charge)"))
    db.add(AuditLog(org_id=org.id, user_id=principal.user_id, action="billing.plan_admin", resource_type="organization", resource_id=str(org.id), details={"plan": body.plan, "charged": False}))
    db.commit()
    return {"plan": org.plan, "credits_balance": org.credits_balance, "charged": False}


@router.post("/billing/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured")
    import stripe

    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature") from exc
    if event.get("type") != "checkout.session.completed":
        return {"received": True, "ignored": True}
    data = event["data"]["object"]
    metadata = data.get("metadata") or {}
    plan = metadata.get("plan")
    org_id = metadata.get("org_id")
    if plan not in PLANS or not org_id:
        return {"received": True, "ignored": True}
    reason = f"stripe:{event['id']}"
    if db.query(CreditLedger).filter(CreditLedger.reason == reason).one_or_none():
        return {"received": True, "duplicate": True}
    org = db.query(Organization).filter(Organization.id == uuid.UUID(str(org_id))).one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.plan = plan
    org.credits_balance = PLANS[plan]["credits"]
    if data.get("customer"):
        org.stripe_customer_id = str(data.get("customer"))
    db.add(CreditLedger(org_id=org.id, delta=PLANS[plan]["credits"], reason=reason))
    db.add(AuditLog(org_id=org.id, user_id=None, action="billing.stripe_webhook", resource_type="organization", resource_id=str(org.id), details={"plan": plan, "event": event["id"]}))
    db.commit()
    return {"received": True}


@router.get("/admin/users")
def list_users(principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = db.query(User).filter(User.org_id == principal.org_id).order_by(User.created_at.asc()).all()
    return [
        {"id": str(row.id), "email": row.email, "full_name": row.full_name, "role": row.role, "status": row.status, "mfa_enabled": row.mfa_enabled, "is_fixture": row.is_fixture}
        for row in rows
    ]


@router.post("/admin/users")
def invite_user(body: UserIn, principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    if body.role not in {"admin", "investigator", "analyst", "viewer", "billing"}:
        raise HTTPException(status_code=422, detail="Role cannot be assigned")
    problem = validate_password(body.password)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).one_or_none():
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(org_id=principal.org_id, email=email, full_name=body.full_name.strip(), role=body.role, password_hash=hash_password(body.password), is_fixture=False)
    db.add(user)
    db.flush()
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="user.invite", resource_type="user", resource_id=str(user.id), details={"role": body.role}))
    db.commit()
    return {"id": str(user.id), "email": user.email, "role": user.role}


@router.patch("/admin/users/{user_id}")
def patch_user(user_id: uuid.UUID, body: UserPatch, principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.org_id == principal.org_id).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role:
        if body.role not in {"owner", "admin", "investigator", "analyst", "viewer", "billing"}:
            raise HTTPException(status_code=422, detail="Unknown role")
        if user.role == "owner" and body.role != user.role and principal.role != "owner":
            raise HTTPException(status_code=422, detail="Only an owner can change an owner's role")
        if body.role == "owner" and principal.role != "owner":
            raise HTTPException(status_code=422, detail="Only an owner can assign the owner role")
        if user.role == "owner" and body.role != "owner":
            owners = db.query(User).filter(User.org_id == principal.org_id, User.role == "owner", User.status == "active").count()
            if owners <= 1:
                raise HTTPException(status_code=422, detail="The organization needs an owner")
        user.role = body.role
    if body.status:
        if body.status not in {"active", "disabled"}:
            raise HTTPException(status_code=422, detail="Unsupported status")
        if body.status != user.status and user.role == "owner" and principal.role != "owner":
            raise HTTPException(status_code=422, detail="Only an owner can change an owner's status")
        if body.status == "disabled" and user.role == "owner":
            owners = db.query(User).filter(User.org_id == principal.org_id, User.role == "owner", User.status == "active").count()
            if owners <= 1:
                raise HTTPException(status_code=422, detail="The organization needs an active owner")
        user.status = body.status
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="user.role_change", resource_type="user", resource_id=str(user.id), details={"role": user.role, "status": user.status}))
    db.commit()
    return {"id": str(user.id), "role": user.role, "status": user.status}


@router.get("/admin/teams")
def list_teams(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    teams = db.query(Team).filter(Team.org_id == principal.org_id).all()
    payload = []
    for team in teams:
        members = db.query(TeamMember).filter(TeamMember.team_id == team.id).all()
        payload.append({
            "id": str(team.id),
            "name": team.name,
            "is_fixture": team.is_fixture,
            "members": [str(member.user_id) for member in members],
        })
    return payload


@router.post("/admin/teams")
def create_team(body: TeamIn, principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    team = Team(org_id=principal.org_id, name=body.name.strip(), is_fixture=False)
    db.add(team)
    db.commit()
    return {"id": str(team.id), "name": team.name}


@router.post("/admin/teams/{team_id}/members")
def add_member(team_id: uuid.UUID, body: MemberIn, principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id, Team.org_id == principal.org_id).one_or_none()
    user = db.query(User).filter(User.id == body.user_id, User.org_id == principal.org_id).one_or_none()
    if not team or not user:
        raise HTTPException(status_code=404, detail="Team or user not found")
    existing = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.user_id == user.id).one_or_none()
    if not existing:
        db.add(TeamMember(team_id=team.id, user_id=user.id))
        db.commit()
    return {"team_id": str(team.id), "user_id": str(user.id)}


@router.get("/admin/audit")
def audit(principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).filter(AuditLog.org_id == principal.org_id).order_by(AuditLog.created_at.desc()).limit(100).all()
    return [
        {
            "id": str(row.id),
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "ip": row.ip,
            "details": row.details or {},
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/admin/retention")
def get_retention(principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    org = _org(db, principal)
    return {"days": org.retention_days}


@router.put("/admin/retention")
def put_retention(body: RetentionIn, principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    org = _org(db, principal)
    org.retention_days = body.days
    db.add(AuditLog(org_id=org.id, user_id=principal.user_id, action="retention.update", resource_type="organization", resource_id=str(org.id), details={"days": body.days}))
    db.commit()
    return {"days": org.retention_days}


@router.post("/admin/retention/run")
def run_retention(principal: Principal = Depends(require("admin")), db: Session = Depends(get_db)):
    result = apply_retention(db, principal.org_id)
    db.add(AuditLog(org_id=principal.org_id, user_id=principal.user_id, action="retention.run", resource_type="organization", resource_id=str(principal.org_id), details=result))
    db.commit()
    return result


@router.post("/gdpr/export")
def gdpr_export(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    require_session(principal)
    user = db.query(User).filter(User.id == principal.user_id).one()
    org = _org(db, principal)
    consents = db.query(ConsentRecord).filter(ConsentRecord.user_id == user.id).all()
    audits = db.query(AuditLog).filter(AuditLog.user_id == user.id).order_by(AuditLog.created_at.desc()).limit(200).all()
    keys = db.query(ApiKey).filter(ApiKey.created_by == user.id).all()
    investigations = db.query(Investigation).filter(Investigation.created_by == user.id).all()
    db.add(AuditLog(org_id=org.id, user_id=user.id, action="gdpr.export", resource_type="user", resource_id=str(user.id), details={}))
    db.commit()
    return {
        "user": {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role, "mfa_enabled": user.mfa_enabled, "is_fixture": user.is_fixture},
        "organization": {"name": org.name, "plan": org.plan},
        "consents": [{"purpose": row.purpose, "lawful_basis": row.lawful_basis, "subject_type": row.subject_type, "text_version": row.text_version, "granted_at": row.granted_at.isoformat()} for row in consents],
        "audit": [{"action": row.action, "created_at": row.created_at.isoformat()} for row in audits],
        "api_keys": [{"prefix": row.key_prefix, "name": row.name, "revoked": row.revoked_at is not None} for row in keys],
        "investigations": [{"id": str(row.id), "title": row.title, "purpose": row.purpose} for row in investigations],
        "note": "Third-party findings are organization records and are not included in this personal export. They follow the retention policy.",
    }


@router.post("/gdpr/delete")
def gdpr_delete(principal: Principal = Depends(require("read")), db: Session = Depends(get_db)):
    require_session(principal)
    user = db.query(User).filter(User.id == principal.user_id).one()
    if user.role == "owner":
        owners = db.query(User).filter(User.org_id == user.org_id, User.role == "owner", User.status == "active").count()
        if owners <= 1:
            raise HTTPException(status_code=422, detail="Transfer ownership before deleting the only owner")
    user.email = f"deleted-{user.id}@redacted.invalid"
    user.full_name = "Deleted user"
    user.password_hash = hash_password(secrets.token_urlsafe(18) + "a1")
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.mfa_pending_secret_encrypted = None
    user.status = "deleted"
    db.query(ConsentRecord).filter(ConsentRecord.user_id == user.id).delete(synchronize_session=False)
    for key in db.query(ApiKey).filter(ApiKey.created_by == user.id).all():
        key.revoked_at = utcnow()
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action="gdpr.delete", resource_type="user", resource_id=str(user.id), details={"anonymized": True}))
    db.commit()
    return {"deleted": True, "anonymized": True}
