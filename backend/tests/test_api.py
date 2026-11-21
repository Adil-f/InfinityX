import uuid

import pyotp

from app.config import settings
from app.db import SessionLocal
from app.models import Finding as FindingRow
from app.models import Organization, User


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _register(client, role_prefix="owner"):
    email = f"{role_prefix}-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Correct-Horse-12",
            "full_name": "Case Analyst",
            "organization": f"Org {uuid.uuid4().hex[:6]}",
            "accept_terms": True,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return body["access_token"], email, body["user"]


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "ok"
    assert body["redis"] in {"ok", "unavailable"}
    assert "covert" in body["boundaries"]


def test_phone_cnic_forensics_graph_and_report(client):
    token, email, user = _register(client)
    headers = _auth(token)
    created = client.post(
        "/api/v1/investigations",
        headers=headers,
        json={"title": "Mail route", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert created.status_code == 200, created.text
    investigation_id = created.json()["id"]

    phone = client.post(
        "/api/v1/search",
        headers=headers,
        json={
            "query": "+393331234567",
            "module": "phone",
            "purpose": "Authorized security investigation",
            "lawful_basis": "legitimate_interest",
            "investigation_id": investigation_id,
        },
    )
    assert phone.status_code == 200, phone.text
    body = phone.json()
    assert body["credits_charged"] == 0
    assert body["findings"][0]["attributes"]["region_code"] == "IT"
    assert body["findings"][0]["attributes"]["subscriber_lookup"] is False

    denied = client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "35202-1234567-1", "module": "cnic", "purpose": "Authorized security investigation", "lawful_basis": "legal_obligation"},
    )
    assert denied.status_code == 422

    cnic = client.post(
        "/api/v1/search",
        headers=headers,
        json={
            "query": "35202-1234567-1",
            "module": "cnic",
            "purpose": "Authorized security investigation",
            "lawful_basis": "legal_obligation",
            "consent": True,
            "investigation_id": investigation_id,
        },
    )
    assert cnic.status_code == 200, cnic.text
    assert "35202-1234567-1" not in cnic.text
    assert "3520212345671" not in cnic.text
    assert cnic.json()["unavailable"][0]["source_id"] == "authorized_identity"
    db = SessionLocal()
    try:
        stored = " ".join(row.value for row in db.query(FindingRow).all())
        assert "35202-1234567-1" not in stored
        assert "3520212345671" not in stored
    finally:
        db.close()

    ambiguous = client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "3520212345671", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert ambiguous.status_code == 200
    assert ambiguous.json()["status"] == "needs_disambiguation"

    hashed = client.post(
        "/api/v1/forensics",
        headers=headers,
        json={"text": "abc", "filename": "note.txt", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest", "investigation_id": investigation_id},
    )
    assert hashed.status_code == 200, hashed.text
    assert hashed.json()["findings"][0]["attributes"]["sha256"].startswith("ba7816bf")

    graph = client.get(f"/api/v1/investigations/{investigation_id}/graph", headers=headers)
    assert graph.status_code == 200
    nodes = graph.json()["nodes"]
    assert len(nodes) >= 2
    edge = client.post(
        f"/api/v1/investigations/{investigation_id}/graph/edges",
        headers=headers,
        json={
            "from_node": nodes[0]["id"],
            "to_node": nodes[1]["id"],
            "relation": "same_person",
            "evidence": "This should be rejected",
            "source_id": "analyst_record",
        },
    )
    assert edge.status_code == 422

    allowed = client.post(
        f"/api/v1/investigations/{investigation_id}/graph/edges",
        headers=headers,
        json={
            "from_node": nodes[0]["id"],
            "to_node": nodes[1]["id"],
            "relation": "has_txt",
            "evidence": "Analyst recorded a public text association",
            "source_id": "analyst_record",
            "confidence": 0.9,
        },
    )
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["confidence"] == 0.4

    analysis = client.post(f"/api/v1/investigations/{investigation_id}/ai", headers=headers)
    assert analysis.status_code == 200, analysis.text
    assert analysis.json()["accuses_person"] is False
    assert "guilty" not in analysis.text.lower()

    report = client.post(
        f"/api/v1/investigations/{investigation_id}/reports",
        headers=headers,
        json={"title": "Case note"},
    )
    assert report.status_code == 200, report.text
    assert "does not accuse" in report.json()["body_markdown"].lower()

    listed = client.get("/api/v1/reports", headers=headers)
    assert any(item["title"] == "Case note" for item in listed.json())

    other_token, _, _ = _register(client, "other")
    foreign = client.get(f"/api/v1/investigations/{investigation_id}", headers=_auth(other_token))
    assert foreign.status_code == 404

    invite = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={"email": f"view-{uuid.uuid4().hex[:8]}@example.com", "full_name": "Viewer", "role": "viewer", "password": "Correct-Horse-12"},
    )
    assert invite.status_code == 200, invite.text
    viewer_login = client.post("/api/v1/auth/login", json={"email": invite.json()["email"], "password": "Correct-Horse-12"})
    assert viewer_login.status_code == 200
    forbidden = client.post(
        "/api/v1/search",
        headers=_auth(viewer_login.json()["access_token"]),
        json={"query": "+923001234567", "module": "phone", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert forbidden.status_code == 403

    sources = client.get("/api/v1/sources", headers=headers)
    hibp = next(item for item in sources.json() if item["id"] == "hibp")
    assert hibp["configuration"] == "unavailable"
    assert "HIBP_API_KEY" in hibp["missing_env"]

    checkout = client.post("/api/v1/billing/checkout", headers=headers, json={"plan": "pro"})
    assert checkout.status_code == 200
    assert checkout.json()["status"] == "unavailable"
    assert checkout.json()["charged"] is False

    plan = client.post("/api/v1/billing/plan", headers=headers, json={"plan": "pro"})
    assert plan.status_code == 200
    assert plan.json()["charged"] is False
    assert plan.json()["plan"] == "pro"

    webhook = client.post("/api/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=bad"})
    assert webhook.status_code == 503
    settings.stripe_webhook_secret = "whsec_test_secret_value"
    try:
        bad = client.post("/api/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=bad"})
        assert bad.status_code == 400
    finally:
        settings.stripe_webhook_secret = None

    key = client.post("/api/v1/api-keys", headers=headers, json={"name": "integration", "scopes": ["search", "read"]})
    assert key.status_code == 200, key.text
    token_value = key.json()["token"]
    via_key = client.post(
        "/api/v1/search",
        headers={"X-API-Key": token_value},
        json={"query": "+923001234567", "module": "phone", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert via_key.status_code == 200, via_key.text
    assert via_key.json()["findings"][0]["attributes"]["region_code"] == "PK"

    exported = client.post("/api/v1/gdpr/export", headers=headers)
    assert exported.status_code == 200
    assert exported.json()["user"]["email"] == email
    assert "password" not in exported.text

    overview = client.get("/api/v1/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["counts"]["investigations"] >= 1

    retention = client.put("/api/v1/admin/retention", headers=headers, json={"days": 30})
    assert retention.status_code == 200
    assert retention.json()["days"] == 30

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert "search" in me.json()["permissions"]


def test_mfa_and_lockout(client):
    token, email, _user = _register(client, "mfa")
    headers = _auth(token)
    setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200, setup.text
    code = pyotp.TOTP(setup.json()["secret"]).now()
    verified = client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": code})
    assert verified.status_code == 200, verified.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Correct-Horse-12"})
    assert login.status_code == 200
    assert login.json()["mfa_required"] is True
    done = client.post("/api/v1/auth/mfa/login", json={"mfa_token": login.json()["mfa_token"], "code": pyotp.TOTP(setup.json()["secret"]).now()})
    assert done.status_code == 200, done.text
    assert "access_token" in done.json()

    locked_email = f"lock-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": locked_email, "password": "Correct-Horse-12", "full_name": "Locked User", "organization": "Lock Org", "accept_terms": True},
    )
    for _ in range(5):
        failed = client.post("/api/v1/auth/login", json={"email": locked_email, "password": "wrong-password-1"})
        assert failed.status_code == 401
    locked = client.post("/api/v1/auth/login", json={"email": locked_email, "password": "Correct-Horse-12"})
    assert locked.status_code == 423


def test_insufficient_credits_do_not_invent_a_result(client):
    token, _email, user = _register(client, "credits")
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.id == user["org_id"]).one()
        org.credits_balance = 0
        db.commit()
    finally:
        db.close()
    response = client.post(
        "/api/v1/search",
        headers=_auth(token),
        json={"query": "example.com", "module": "domain", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert response.status_code == 402
    assert "example.com" not in response.text or "Insufficient" in response.text
    assert "findings" not in response.json()
