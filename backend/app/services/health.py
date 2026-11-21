from __future__ import annotations

import httpx

from app.config import settings
from app.connectors.catalog import connector_by_id, missing_env
from app.security import USER_AGENT
from app.services.dns_source import cymru_asn, dns_lookup
from app.services.http_sources import crtsh_domain, gitlab_user, gravatar_exists, rdap_domain, ripestat_prefix, urlhaus_host


def _from_outcome(outcome) -> dict:
    status = "ok" if outcome.status in {"ok", "not_found"} else outcome.status
    return {
        "status": status,
        "detail": outcome.error or outcome.message or outcome.status,
    }


def probe_connector(source_id: str) -> dict:
    spec = connector_by_id(source_id)
    if not spec:
        return {"status": "error", "detail": "Unknown source"}
    missing = missing_env(spec, settings)
    if missing:
        return {"status": "unavailable", "detail": "Missing configuration", "required_env": missing}
    if spec["category"] == "local":
        return {"status": "ok", "detail": "Local module is available"}
    try:
        if source_id == "dns":
            return _from_outcome(dns_lookup("example.com", enforce_limit=False))
        if source_id == "rdap":
            return _from_outcome(rdap_domain("example.com"))
        if source_id == "crtsh":
            return _from_outcome(crtsh_domain("example.com"))
        if source_id == "team_cymru":
            return _from_outcome(cymru_asn("8.8.8.8", enforce_limit=False))
        if source_id == "ripestat":
            return _from_outcome(ripestat_prefix("8.8.8.8"))
        if source_id == "github":
            headers = {"User-Agent": USER_AGENT}
            if settings.github_token:
                headers["Authorization"] = f"Bearer {settings.github_token}"
            response = httpx.get("https://api.github.com/rate_limit", headers=headers, timeout=10)
            if response.status_code == 200:
                return {"status": "ok", "detail": "GitHub rate-limit endpoint responded"}
            return {"status": "error", "detail": f"GitHub HTTP {response.status_code}"}
        if source_id == "gitlab":
            return _from_outcome(gitlab_user("gitlab-org"))
        if source_id == "gravatar":
            return _from_outcome(gravatar_exists("health-check@example.com"))
        if source_id == "urlhaus":
            return _from_outcome(urlhaus_host("example.com"))
        if source_id == "hibp":
            response = httpx.get("https://haveibeenpwned.com/api/v3/breachedaccount/health-check@example.com", headers={"hibp-api-key": settings.hibp_api_key or "", "User-Agent": USER_AGENT}, timeout=12)
            if response.status_code in {200, 404}:
                return {"status": "ok", "detail": f"HIBP responded HTTP {response.status_code}"}
            return {"status": "error", "detail": f"HIBP HTTP {response.status_code}"}
        if source_id == "virustotal":
            response = httpx.get("https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8", headers={"x-apikey": settings.virustotal_api_key or "", "User-Agent": USER_AGENT}, timeout=15)
            if response.status_code in {200, 404}:
                return {"status": "ok", "detail": f"VirusTotal responded HTTP {response.status_code}"}
            return {"status": "error", "detail": f"VirusTotal HTTP {response.status_code}"}
        if source_id == "otx":
            response = httpx.get("https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general", headers={"X-OTX-API-KEY": settings.otx_api_key or "", "User-Agent": USER_AGENT}, timeout=12)
            if response.status_code == 200:
                return {"status": "ok", "detail": "OTX responded"}
            return {"status": "error", "detail": f"OTX HTTP {response.status_code}"}
        if source_id == "authorized_identity":
            response = httpx.get(settings.authorized_identity_provider_url, headers={"User-Agent": USER_AGENT}, timeout=10, follow_redirects=False)
            return {"status": "ok" if response.status_code < 500 else "error", "detail": f"Reachability HTTP {response.status_code}. No identifier was sent."}
        if source_id == "stripe":
            import stripe

            stripe.api_key = settings.stripe_secret_key
            stripe.Balance.retrieve()
            return {"status": "ok", "detail": "Stripe balance endpoint responded. No charge was created."}
    except Exception as exc:
        return {"status": "error", "detail": f"{type(exc).__name__}: {exc}"[:300]}
    return {"status": "error", "detail": "No probe is implemented for this source"}
