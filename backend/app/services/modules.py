from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from email_validator import EmailNotValidError, validate_email

from app.services.classify import classify_query, is_ip, normalize_domain
from app.services.cnic import inspect_cnic
from app.services.dns_source import cymru_asn, dns_lookup, reverse_dns
from app.services.http_sources import (
    crtsh_domain,
    github_user,
    gitlab_user,
    gravatar_exists,
    hibp_email,
    otx_indicator,
    rdap_domain,
    ripestat_prefix,
    unverified_handle_templates,
    urlhaus_host,
    virustotal_indicator,
)
from app.services.phone import inspect_phone
from app.services.results import Finding, ModuleResult, absorb, dedupe_findings

DISPOSABLE_HINTS = {
    "mailinator.com",
    "guerrillamail.com",
    "tempmail.com",
    "10minutemail.com",
    "yopmail.com",
}


def _disabled_outcome(source_id: str, source_name: str):
    from app.services.results import SourceOutcome

    return SourceOutcome(
        source_id=source_id,
        source_name=source_name,
        status="unavailable",
        message="Disabled by an administrator. The source was not queried.",
    )


def _run_if_enabled(source_id: str, source_name: str, disabled: set[str], func):
    if source_id in disabled:
        return _disabled_outcome(source_id, source_name), False
    return func(), True


def run_email(query: str, disabled: set[str] | None = None) -> ModuleResult:
    disabled = disabled or set()
    result = ModuleResult(query_type="email", normalized_query=query.strip().lower())
    try:
        valid = validate_email(query.strip(), check_deliverability=False)
        email = valid.normalized
    except EmailNotValidError as exc:
        result.status = "rejected"
        result.errors.append({"source_id": "local_normalizer", "source_name": "Local normalizer", "message": str(exc)})
        return result
    result.normalized_query = email
    domain = email.split("@", 1)[1]
    result.findings.append(
        Finding(
            entity_type="email",
            value=email,
            normalized_value=email,
            title="Email syntax",
            summary=f"{email} is syntactically valid. This does not prove the mailbox exists.",
            source_id="local_normalizer",
            source_name="Local normalizer",
            confidence=0.95,
            verified=True,
            kind="fact",
            attributes={"links": [{"relation": "has_domain", "target_type": "domain", "target_value": domain, "evidence": "Email domain"}]},
        )
    )
    if domain in DISPOSABLE_HINTS:
        result.findings.append(
            Finding(
                entity_type="domain",
                value=domain,
                normalized_value=domain,
                title="Disposable-domain hint",
                summary=f"{domain} is on the built-in short list of well-known disposable mail domains. The list is not exhaustive and is not a live feed.",
                source_id="local_normalizer",
                source_name="Local disposable-domain reference list",
                confidence=0.7,
                verified=True,
                kind="fact",
                attributes={"reference_list": True, "live_query": False, "exhaustive": False},
            )
        )
    dns_outcome, attempted = _run_if_enabled("dns", "DNS", disabled, lambda: dns_lookup(domain))
    result.external_attempted = result.external_attempted or attempted
    absorb(result, dns_outcome)
    gravatar_outcome, attempted = _run_if_enabled("gravatar", "Gravatar", disabled, lambda: gravatar_exists(email))
    result.external_attempted = result.external_attempted or attempted
    absorb(result, gravatar_outcome)
    hibp_outcome, attempted = _run_if_enabled("hibp", "Have I Been Pwned", disabled, lambda: hibp_email(email))
    result.external_attempted = result.external_attempted or attempted
    absorb(result, hibp_outcome)
    result.notes.append("Domain registration and certificate transparency are available on the Domain module.")
    return result


def run_domain(query: str, disabled: set[str] | None = None) -> ModuleResult:
    disabled = disabled or set()
    domain = normalize_domain(query)
    result = ModuleResult(query_type="domain", normalized_query=domain or query.strip().lower())
    if not domain or is_ip(query.strip()):
        result.status = "rejected"
        result.suggested_module = "ip" if is_ip(query.strip()) else None
        result.errors.append({
            "source_id": "local_normalizer",
            "source_name": "Local normalizer",
            "message": "This value is not a domain name." + (" Use the IP module." if result.suggested_module == "ip" else ""),
            "suggested_module": result.suggested_module,
        })
        return result
    tasks = []
    if "dns" not in disabled:
        tasks.append(("dns", lambda: dns_lookup(domain)))
    else:
        absorb(result, _disabled_outcome("dns", "DNS"))
    if "rdap" not in disabled:
        tasks.append(("rdap", lambda: rdap_domain(domain)))
    else:
        absorb(result, _disabled_outcome("rdap", "RDAP"))
    if "crtsh" not in disabled:
        tasks.append(("crtsh", lambda: crtsh_domain(domain)))
    else:
        absorb(result, _disabled_outcome("crtsh", "crt.sh"))
    if tasks:
        result.external_attempted = True
        with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            futures = [pool.submit(func) for _, func in tasks]
            for future in futures:
                absorb(result, future.result())
    result.notes.append("Reputation feeds for this domain are on the Threat module.")
    return result


def run_ip(query: str, disabled: set[str] | None = None) -> ModuleResult:
    disabled = disabled or set()
    raw = query.strip()
    result = ModuleResult(query_type="ip", normalized_query=raw)
    if not is_ip(raw):
        result.status = "rejected"
        result.errors.append({"source_id": "local_normalizer", "source_name": "Local normalizer", "message": "This value is not an IP address."})
        return result
    import ipaddress

    ip = str(ipaddress.ip_address(raw))
    result.normalized_query = ip
    tasks = []
    for source_id, source_name, func in (
        ("dns", "DNS", lambda: reverse_dns(ip)),
        ("team_cymru", "Team Cymru ASN", lambda: cymru_asn(ip)),
        ("ripestat", "RIPEstat", lambda: ripestat_prefix(ip)),
    ):
        if source_id in disabled:
            absorb(result, _disabled_outcome(source_id, source_name))
        else:
            tasks.append(func)
    if tasks:
        result.external_attempted = True
        with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            for future in [pool.submit(func) for func in tasks]:
                absorb(result, future.result())
    result.notes.append("Network registration country is not a device location. Reputation feeds are on the Threat module.")
    return result


def _indicator(query: str) -> tuple[str, str] | None:
    raw = query.strip()
    if raw.lower().startswith("http://") or raw.lower().startswith("https://"):
        from urllib.parse import urlparse

        host = urlparse(raw).hostname
        if not host:
            return None
        kind = "ip" if is_ip(host) else "domain"
        return kind, host.lower()
    if is_ip(raw):
        import ipaddress

        return "ip", str(ipaddress.ip_address(raw))
    if re.fullmatch(r"[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", raw):
        return "hash", raw.lower()
    domain = normalize_domain(raw)
    if domain:
        return "domain", domain
    return None


def run_threat(query: str, disabled: set[str] | None = None) -> ModuleResult:
    disabled = disabled or set()
    parsed = _indicator(query)
    result = ModuleResult(query_type="threat", normalized_query=query.strip())
    if not parsed:
        result.status = "rejected"
        result.errors.append({
            "source_id": "local_normalizer",
            "source_name": "Local normalizer",
            "message": "Threat checks accept an IP, domain, URL, or MD5/SHA-1/SHA-256 hash. The URL itself is not fetched.",
        })
        return result
    kind, value = parsed
    result.normalized_query = value
    result.notes.append("The submitted URL was not fetched. Only the host or hash is sent to threat sources.")
    if kind in {"ip", "domain"}:
        outcome, attempted = _run_if_enabled("urlhaus", "URLhaus", disabled, lambda: urlhaus_host(value))
        result.external_attempted = result.external_attempted or attempted
        absorb(result, outcome)
    else:
        result.notes.append("URLhaus host lookup does not apply to a file hash.")
    vt_kind = kind
    outcome, attempted = _run_if_enabled("virustotal", "VirusTotal", disabled, lambda: virustotal_indicator(vt_kind, value))
    result.external_attempted = result.external_attempted or attempted
    absorb(result, outcome)
    outcome, attempted = _run_if_enabled("otx", "AlienVault OTX", disabled, lambda: otx_indicator(vt_kind, value))
    result.external_attempted = result.external_attempted or attempted
    absorb(result, outcome)
    return result


def run_handle(query: str, disabled: set[str] | None = None) -> ModuleResult:
    disabled = disabled or set()
    name = query.strip().lstrip("@")
    result = ModuleResult(query_type="username", normalized_query=name)
    if not re.fullmatch(r"[A-Za-z0-9._-]{2,39}", name):
        result.status = "rejected"
        result.errors.append({
            "source_id": "local_normalizer",
            "source_name": "Local normalizer",
            "message": "Username must be 2-39 characters: letters, numbers, dot, underscore, or hyphen.",
        })
        return result
    result.findings.append(
        Finding(
            entity_type="username",
            value=name,
            normalized_value=name.lower(),
            title="Normalized handle",
            summary="Handle syntax accepted. This is not proof that an account exists.",
            source_id="local_normalizer",
            source_name="Local normalizer",
            confidence=1.0,
            verified=True,
            kind="fact",
        )
    )
    for source_id, source_name, func in (
        ("github", "GitHub public API", lambda: github_user(name)),
        ("gitlab", "GitLab public API", lambda: gitlab_user(name)),
    ):
        outcome, attempted = _run_if_enabled(source_id, source_name, disabled, func)
        result.external_attempted = result.external_attempted or attempted
        absorb(result, outcome)
    result.findings.extend(unverified_handle_templates(name))
    result.notes.append("URL templates are not existence checks. No social network was scraped behind a login.")
    return result


def run_phone(query: str, region: str | None = None) -> ModuleResult:
    return inspect_phone(query, region)


def run_cnic(query: str, purpose: str, case_id: str | None = None, disabled: set[str] | None = None) -> ModuleResult:
    from app.services.results import SourceOutcome

    disabled = disabled or set()
    if "authorized_identity" in disabled:
        provider = SourceOutcome(
            source_id="authorized_identity",
            source_name="Authorized identity provider",
            status="unavailable",
            message="Disabled by an administrator. No identity provider was queried.",
        )
        result = inspect_cnic(query, provider)
        result.external_attempted = False
        return result
    result = inspect_cnic(query, SourceOutcome(
        source_id="authorized_identity",
        source_name="Authorized identity provider",
        status="unavailable",
        required_env=[],
        message=(
            "CNIC checks are format validation only. NADRA is not queried. "
            "Setting AUTHORIZED_IDENTITY_PROVIDER_URL or AUTHORIZED_IDENTITY_PROVIDER_TOKEN does not make this search call a provider."
        ),
    ))
    result.external_attempted = False
    result.transient.pop("provider_response", None)
    return result


def run_query(query: str, module: str | None, *, region: str | None = None, purpose: str = "", case_id: str | None = None, disabled: set[str] | None = None) -> ModuleResult:
    disabled = disabled or set()
    routed = classify_query(query, module if module and module != "universal" else None)
    query_type = routed["query_type"]
    if query_type == "ambiguous_numeric":
        return ModuleResult(
            query_type="ambiguous_numeric",
            normalized_query=routed.get("normalized") or query,
            status="needs_disambiguation",
            notes=[routed.get("reason") or "Choose Phone or CNIC."],
            suggested_module=None,
        )
    if query_type == "rejected":
        return ModuleResult(
            query_type="rejected",
            normalized_query=query[:80],
            status="rejected",
            errors=[{"source_id": "local_normalizer", "source_name": "Local normalizer", "message": routed.get("reason") or "Unrecognized query"}],
            suggested_module=routed.get("suggested_module"),
        )
    if query_type == "phone":
        result = run_phone(query, region)
    elif query_type == "cnic":
        result = run_cnic(query, purpose, case_id, disabled)
    elif query_type == "email":
        result = run_email(query, disabled)
    elif query_type == "domain":
        result = run_domain(query, disabled)
    elif query_type == "ip":
        ip_result = run_ip(query, disabled)
        threat_result = run_threat(query, disabled)
        ip_result.findings.extend(threat_result.findings)
        ip_result.unavailable.extend(threat_result.unavailable)
        ip_result.errors.extend(threat_result.errors)
        ip_result.notes.extend(threat_result.notes)
        ip_result.external_attempted = ip_result.external_attempted or threat_result.external_attempted
        result = ip_result
    elif query_type == "url":
        host = routed.get("host")
        if not host:
            return ModuleResult(query_type="rejected", normalized_query=query[:80], status="rejected", errors=[{"source_id": "local_normalizer", "source_name": "Local normalizer", "message": "URL has no host"}])
        domain_result = run_domain(host, disabled) if not is_ip(host) else run_ip(host, disabled)
        threat_result = run_threat(query, disabled)
        domain_result.query_type = "url"
        domain_result.findings.extend(threat_result.findings)
        domain_result.unavailable.extend(threat_result.unavailable)
        domain_result.errors.extend(threat_result.errors)
        domain_result.notes.extend(threat_result.notes)
        domain_result.external_attempted = domain_result.external_attempted or threat_result.external_attempted
        result = domain_result
    elif query_type in {"username", "social"}:
        result = run_handle(query, disabled)
        result.query_type = query_type
    elif query_type == "threat":
        result = run_threat(query, disabled)
    elif query_type == "forensics":
        return ModuleResult(
            query_type="rejected",
            normalized_query="",
            status="rejected",
            errors=[{"source_id": "evidence_hash", "source_name": "Evidence hashing", "message": "Use the forensics endpoint with file content."}],
        )
    else:
        return ModuleResult(query_type="rejected", normalized_query=query[:80], status="rejected", errors=[{"source_id": "local_normalizer", "source_name": "Local normalizer", "message": "Unsupported module"}])
    result.findings = dedupe_findings(result.findings)
    return result
