import uuid

import pyotp

from app.config import settings
from app.db import SessionLocal
from app.models import AuditLog, ConsentRecord, User
from app.services.http_sources import otx_indicator, otx_section
from app.services.ratelimit import MemoryRateLimiter, get_redis, reset_redis_cache
import app.services.ratelimit as ratelimit


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _register(client, prefix="owner"):
    email = f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"
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


def _login(client, email):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Correct-Horse-12"})
    assert response.status_code == 200, response.text
    return response.json()


class RecordingClient:
    def __init__(self):
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)

        class Response:
            status_code = 200

            def json(self):
                return {"pulse_info": {"pulses": []}}

        return Response()


def test_otx_uses_ipv6_section():
    assert otx_section("ip", "2001:4860:4860::8888") == "IPv6"
    assert otx_section("ip", "8.8.8.8") == "IPv4"
    settings.otx_api_key = "test-key"
    try:
        client = RecordingClient()
        outcome = otx_indicator("ip", "2001:4860:4860::8888", client=client)
        assert outcome.status == "ok"
        assert "/IPv6/" in client.urls[0]
    finally:
        settings.otx_api_key = None


def test_redis_connection_failure_is_retried(monkeypatch):
    reset_redis_cache()
    attempts = {"n": 0}

    class Client:
        def ping(self):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise ConnectionError("down")
            return True

    shared = Client()
    monkeypatch.setattr(ratelimit.redis.Redis, "from_url", lambda *args, **kwargs: shared)
    assert get_redis() is None
    assert get_redis() is None
    ratelimit._redis_failed_at -= 10
    assert get_redis() is not None
    assert attempts["n"] == 2
    reset_redis_cache()


def test_public_health_hides_environment(client):
    for path in ("/health", "/api/v1/health"):
        body = client.get(path).json()
        assert "env" not in body
        assert "fixtures_seeded" not in body
        assert body["database"] == "ok"


def test_registration_is_rate_limited(client, monkeypatch):
    limiter = MemoryRateLimiter(limit=1)

    def allow(key, limit):
        if str(key).startswith("register:"):
            return limiter.allow(key)
        return True

    monkeypatch.setattr("app.routers.auth.allow", allow)
    first, _, _ = _register(client, "rate")
    assert first
    blocked = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"rate-{uuid.uuid4().hex[:8]}@example.com",
            "password": "Correct-Horse-12",
            "full_name": "Second",
            "organization": "Second Org",
            "accept_terms": True,
        },
    )
    assert blocked.status_code == 429


def test_api_key_cannot_use_user_session_routes(client):
    token, _, _ = _register(client, "keyuser")
    created = client.post("/api/v1/api-keys", headers=_auth(token), json={"name": "search", "scopes": ["search", "read"]})
    assert created.status_code == 200, created.text
    key = {"X-API-Key": created.json()["token"]}
    me = client.get("/api/v1/auth/me", headers=key)
    assert me.status_code == 200
    assert me.json()["role"] == "api_key"
    assert me.json()["email"] is None
    assert "admin" not in me.json()["permissions"]
    assert client.post("/api/v1/auth/mfa/setup", headers=key).status_code == 403
    assert client.post("/api/v1/gdpr/export", headers=key).status_code == 403
    assert client.post("/api/v1/gdpr/delete", headers=key).status_code == 403


def test_disabled_creator_loses_api_key(client):
    token, _, owner = _register(client, "disabler")
    email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    invited = client.post(
        "/api/v1/admin/users",
        headers=_auth(token),
        json={"email": email, "full_name": "Admin", "role": "admin", "password": "Correct-Horse-12"},
    )
    assert invited.status_code == 200, invited.text
    analyst = _login(client, email)
    key = client.post("/api/v1/api-keys", headers=_auth(analyst["access_token"]), json={"name": "admin-key", "scopes": ["search"]})
    assert key.status_code == 200, key.text
    users = client.get("/api/v1/admin/users", headers=_auth(token)).json()
    analyst_id = next(row["id"] for row in users if row["email"] == email)
    disabled = client.patch(f"/api/v1/admin/users/{analyst_id}", headers=_auth(token), json={"status": "disabled"})
    assert disabled.status_code == 200, disabled.text
    denied = client.post(
        "/api/v1/search",
        headers={"X-API-Key": key.json()["token"]},
        json={"query": "+923001234567", "module": "phone", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert denied.status_code == 401
    assert owner["role"] == "owner"


def test_billing_key_cannot_gain_search(client):
    token, _, _ = _register(client, "biller")
    email = f"bill-{uuid.uuid4().hex[:8]}@example.com"
    invited = client.post(
        "/api/v1/admin/users",
        headers=_auth(token),
        json={"email": email, "full_name": "Billing", "role": "billing", "password": "Correct-Horse-12"},
    )
    assert invited.status_code == 200, invited.text
    billing = _login(client, email)["access_token"]
    too_wide = client.post("/api/v1/api-keys", headers=_auth(billing), json={"name": "wide", "scopes": ["search", "read"]})
    assert too_wide.status_code == 422
    read_only = client.post("/api/v1/api-keys", headers=_auth(billing), json={"name": "read", "scopes": ["read"]})
    assert read_only.status_code == 200, read_only.text
    search = client.post(
        "/api/v1/search",
        headers={"X-API-Key": read_only.json()["token"]},
        json={"query": "+923001234567", "module": "phone", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert search.status_code == 403


def test_mfa_replacement_and_lockout(client):
    token, email, _ = _register(client, "rotator")
    setup = client.post("/api/v1/auth/mfa/setup", headers=_auth(token))
    secret = setup.json()["secret"]
    assert client.post("/api/v1/auth/mfa/verify", headers=_auth(token), json={"code": pyotp.TOTP(secret).now()}).status_code == 200
    naked = client.post("/api/v1/auth/mfa/setup", headers=_auth(token))
    assert naked.status_code == 401
    login = _login(client, email)
    assert login["mfa_required"] is True
    rotated = client.post("/api/v1/auth/mfa/setup", headers=_auth(token), json={"current_code": pyotp.TOTP(secret).now()})
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["pending"] is True
    assert rotated.json()["enabled"] is True
    still_old = client.post("/api/v1/auth/mfa/login", json={"mfa_token": login["mfa_token"], "code": pyotp.TOTP(secret).now()})
    assert still_old.status_code == 200, still_old.text
    promoted = client.post("/api/v1/auth/mfa/verify", headers=_auth(token), json={"code": pyotp.TOTP(rotated.json()["secret"]).now()})
    assert promoted.status_code == 200

    other, other_email, _ = _register(client, "lockedmfa")
    enrolled = client.post("/api/v1/auth/mfa/setup", headers=_auth(other))
    other_secret = enrolled.json()["secret"]
    client.post("/api/v1/auth/mfa/verify", headers=_auth(other), json={"code": pyotp.TOTP(other_secret).now()})
    pending = _login(client, other_email)
    for _ in range(5):
        failed = client.post("/api/v1/auth/mfa/login", json={"mfa_token": pending["mfa_token"], "code": "000000"})
        assert failed.status_code == 401
    locked = client.post("/api/v1/auth/mfa/login", json={"mfa_token": pending["mfa_token"], "code": pyotp.TOTP(other_secret).now()})
    assert locked.status_code == 423


def test_owner_assignment_and_last_owner_disable(client):
    token, email, _ = _register(client, "sole")
    admin_email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/admin/users",
        headers=_auth(token),
        json={"email": admin_email, "full_name": "Admin", "role": "admin", "password": "Correct-Horse-12"},
    )
    admin = _login(client, admin_email)["access_token"]
    users = client.get("/api/v1/admin/users", headers=_auth(admin)).json()
    target = next(row["id"] for row in users if row["email"] == email)
    promoted = client.patch(f"/api/v1/admin/users/{target}", headers=_auth(admin), json={"role": "owner"})
    assert promoted.status_code == 422
    disabled = client.patch(f"/api/v1/admin/users/{target}", headers=_auth(token), json={"status": "disabled"})
    assert disabled.status_code == 422


def test_connector_toggle_is_per_organization(client):
    first, _, _ = _register(client, "org-a")
    second, _, _ = _register(client, "org-b")
    changed = client.patch("/api/v1/sources/dns", headers=_auth(first), json={"enabled": False})
    assert changed.status_code == 200, changed.text
    a_dns = next(row for row in client.get("/api/v1/sources", headers=_auth(first)).json() if row["id"] == "dns")
    b_dns = next(row for row in client.get("/api/v1/sources", headers=_auth(second)).json() if row["id"] == "dns")
    assert a_dns["enabled"] is False
    assert b_dns["enabled"] is True


def test_manual_edges_cannot_claim_connector_provenance(client):
    token, _, _ = _register(client, "graph")
    headers = _auth(token)
    created = client.post(
        "/api/v1/investigations",
        headers=headers,
        json={"title": "Links", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    investigation = created.json()["id"]
    for query, module, extra in (
        ("+393331234567", "phone", {}),
        ("35202-1234567-1", "cnic", {"consent": True, "lawful_basis": "legal_obligation"}),
    ):
        body = {"query": query, "module": module, "purpose": "Authorized security investigation", "lawful_basis": extra.get("lawful_basis", "legitimate_interest"), "investigation_id": investigation, "consent": extra.get("consent", False)}
        assert client.post("/api/v1/search", headers=headers, json=body).status_code == 200
    nodes = client.get(f"/api/v1/investigations/{investigation}/graph", headers=headers).json()["nodes"]
    edge = client.post(
        f"/api/v1/investigations/{investigation}/graph/edges",
        headers=headers,
        json={"from_node": nodes[0]["id"], "to_node": nodes[1]["id"], "relation": "has_txt", "evidence": "Analyst note recorded in the case file", "source_id": "dns", "confidence": 1},
    )
    assert edge.status_code == 200, edge.text
    assert edge.json()["confidence"] == 0.4
    stored = client.get(f"/api/v1/investigations/{investigation}/graph", headers=headers).json()["edges"][0]
    assert stored["source_id"] == "analyst_record"
    assert stored["analyst_asserted"] is True
    audits = client.get("/api/v1/admin/audit", headers=headers).json()
    recorded = next(row for row in audits if row["action"] == "graph.edge")
    assert recorded["details"]["source_id"] == "analyst_record"


def test_vendor_health_does_not_call_shared_credentials(client, monkeypatch):
    token, _, _ = _register(client, "health")
    called = {"n": 0}

    def boom(source_id):
        called["n"] += 1
        raise AssertionError(source_id)

    monkeypatch.setattr("app.routers.platform.probe_connector", boom)
    settings.hibp_api_key = "should-not-be-sent"
    try:
        response = client.post("/api/v1/sources/hibp/health", headers=_auth(token))
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "not_probed"
        assert called["n"] == 0
    finally:
        settings.hibp_api_key = None


def test_github_health_probes_the_public_api(client, monkeypatch):
    token, _, _ = _register(client, "github-health")
    seen = {}

    def fake(source_id):
        seen["id"] = source_id
        return {"status": "ok", "detail": "GitHub rate-limit endpoint responded"}

    monkeypatch.setattr("app.routers.platform.probe_connector", fake)
    response = client.post("/api/v1/sources/github/health", headers=_auth(token))
    assert response.status_code == 200, response.text
    assert seen["id"] == "github"
    assert response.json()["status"] == "ok"


def test_gdpr_delete_clears_pending_mfa(client):
    owner, _, _ = _register(client, "gdpr-owner")
    email = f"member-{uuid.uuid4().hex[:8]}@example.com"
    invited = client.post(
        "/api/v1/admin/users",
        headers=_auth(owner),
        json={"email": email, "full_name": "Member", "role": "analyst", "password": "Correct-Horse-12"},
    )
    assert invited.status_code == 200, invited.text
    member_id = invited.json()["id"]
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == member_id).one()
        user.mfa_secret_encrypted = "active-secret"
        user.mfa_pending_secret_encrypted = "pending-secret"
        user.mfa_enabled = False
        db.commit()
    finally:
        db.close()
    member = _login(client, email)["access_token"]
    deleted = client.post("/api/v1/gdpr/delete", headers=_auth(member))
    assert deleted.status_code == 200, deleted.text
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == member_id).one()
        assert user.mfa_secret_encrypted is None
        assert user.mfa_pending_secret_encrypted is None
        assert user.mfa_enabled is False
    finally:
        db.close()


def test_api_key_search_attributes_consent_to_creator(client):
    token, _, owner = _register(client, "key-audit")
    created = client.post("/api/v1/api-keys", headers=_auth(token), json={"name": "search", "scopes": ["search"]})
    assert created.status_code == 200, created.text
    searched = client.post(
        "/api/v1/search",
        headers={"X-API-Key": created.json()["token"]},
        json={"query": "+923001234567", "module": "phone", "purpose": "Authorized security investigation", "lawful_basis": "legitimate_interest"},
    )
    assert searched.status_code == 200, searched.text
    me = client.get("/api/v1/auth/me", headers={"X-API-Key": created.json()["token"]})
    assert me.json()["role"] == "api_key"
    db = SessionLocal()
    try:
        consent = db.query(ConsentRecord).filter(ConsentRecord.user_id == owner["id"], ConsentRecord.subject_type == "phone").one()
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == owner["id"], AuditLog.action == "search.run", AuditLog.resource_id == searched.json()["job_id"])
            .one()
        )
        assert consent.purpose.startswith("Authorized")
        assert audit.user_id is not None
    finally:
        db.close()


def test_admin_cannot_demote_an_owner(client):
    token, _, _ = _register(client, "demote")
    headers = _auth(token)
    second = f"second-{uuid.uuid4().hex[:8]}@example.com"
    admin = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    for email, role in ((second, "investigator"), (admin, "admin")):
        assert client.post(
            "/api/v1/admin/users",
            headers=headers,
            json={"email": email, "full_name": role, "role": role, "password": "Correct-Horse-12"},
        ).status_code == 200
    users = client.get("/api/v1/admin/users", headers=headers).json()
    second_id = next(row["id"] for row in users if row["email"] == second)
    promoted = client.patch(f"/api/v1/admin/users/{second_id}", headers=headers, json={"role": "owner"})
    assert promoted.status_code == 200, promoted.text
    admin_token = _login(client, admin)["access_token"]
    demoted = client.patch(f"/api/v1/admin/users/{second_id}", headers=_auth(admin_token), json={"role": "analyst"})
    assert demoted.status_code == 422
