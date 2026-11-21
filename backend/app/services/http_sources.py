from __future__ import annotations

import hashlib
from urllib.parse import quote

import httpx

from app.config import settings
from app.security import USER_AGENT
from app.services.results import Finding, SourceOutcome

_client: httpx.Client | None = None


def default_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=12, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    return _client


def _truncate(value: str) -> str:
    return (value or "")[:300]


def parse_rdap_payload(domain: str, payload: dict) -> list[Finding]:
    findings: list[Finding] = []
    ldh = str(payload.get("ldhName") or domain).lower()
    statuses = payload.get("status") or []
    if statuses:
        findings.append(
            Finding(
                entity_type="domain",
                value=ldh,
                normalized_value=ldh,
                title="RDAP status",
                summary=f"RDAP lists {ldh} with status {', '.join(statuses)}.",
                source_id="rdap",
                source_name="RDAP",
                source_url=f"https://rdap.org/domain/{quote(domain)}",
                confidence=0.9,
                verified=True,
                kind="fact",
                attributes={"status": statuses},
            )
        )
    for nameserver in payload.get("nameservers") or []:
        host = str(nameserver.get("ldhName") or "").rstrip(".").lower()
        if not host:
            continue
        findings.append(
            Finding(
                entity_type="host",
                value=host,
                normalized_value=host,
                title="RDAP nameserver",
                summary=f"RDAP nameserver for {ldh}: {host}.",
                source_id="rdap",
                source_name="RDAP",
                source_url=f"https://rdap.org/domain/{quote(domain)}",
                confidence=0.9,
                verified=True,
                kind="fact",
                attributes={"links": [{"relation": "has_ns", "target_type": "host", "target_value": host, "evidence": f"RDAP nameserver {host}"}]},
            )
        )
    for event in payload.get("events") or []:
        action = event.get("eventAction")
        date = event.get("eventDate")
        if action and date:
            findings.append(
                Finding(
                    entity_type="domain",
                    value=f"{action} {date}",
                    normalized_value=ldh,
                    title=f"RDAP {action}",
                    summary=f"RDAP {action} event for {ldh} is {date}.",
                    source_id="rdap",
                    source_name="RDAP",
                    source_url=f"https://rdap.org/domain/{quote(domain)}",
                    confidence=0.85,
                    verified=True,
                    kind="fact",
                    attributes={"event_action": action, "event_date": date},
                )
            )
    for entity in payload.get("entities") or []:
        roles = [str(role).lower() for role in entity.get("roles") or []]
        if "registrar" not in roles:
            continue
        fn = _vcard_fn(entity.get("vcardArray"))
        if not fn:
            continue
        findings.append(
            Finding(
                entity_type="organization",
                value=fn,
                normalized_value=fn.lower(),
                title="RDAP registrar",
                summary=f"RDAP registrar for {ldh} is {fn}.",
                source_id="rdap",
                source_name="RDAP",
                source_url=f"https://rdap.org/domain/{quote(domain)}",
                confidence=0.85,
                verified=True,
                kind="fact",
                attributes={"links": [{"relation": "has_registrar", "target_type": "organization", "target_value": fn, "evidence": f"RDAP registrar {fn}"}]},
            )
        )
    if not findings:
        findings.append(
            Finding(
                entity_type="domain",
                value=ldh,
                normalized_value=ldh,
                title="RDAP record",
                summary=f"RDAP returned a record for {ldh} without registrar, nameserver, or event fields in the parsed subset.",
                source_id="rdap",
                source_name="RDAP",
                source_url=f"https://rdap.org/domain/{quote(domain)}",
                confidence=0.5,
                verified=True,
                kind="fact",
            )
        )
    return findings


def _vcard_fn(vcard) -> str | None:
    if not isinstance(vcard, list) or len(vcard) < 2 or not isinstance(vcard[1], list):
        return None
    for item in vcard[1]:
        if isinstance(item, list) and item and item[0] == "fn" and len(item) >= 4:
            return str(item[3])
    return None


def rdap_domain(domain: str, client=None) -> SourceOutcome:
    url = f"https://rdap.org/domain/{quote(domain)}"
    client = client or default_client()
    try:
        response = client.get(url, headers={"Accept": "application/rdap+json, application/json", "User-Agent": USER_AGENT}, timeout=12)
    except Exception as exc:
        return SourceOutcome(source_id="rdap", source_name="RDAP", status="error", error=_truncate(f"{type(exc).__name__}: {exc}"))
    if response.status_code == 404:
        return SourceOutcome(
            source_id="rdap",
            source_name="RDAP",
            status="not_found",
            findings=[
                Finding(
                    entity_type="domain",
                    value=domain,
                    normalized_value=domain,
                    title="RDAP",
                    summary=f"RDAP returned 404 for {domain}.",
                    source_id="rdap",
                    source_name="RDAP",
                    source_url=url,
                    confidence=0.8,
                    verified=True,
                    kind="fact",
                )
            ],
        )
    if response.status_code >= 400:
        return SourceOutcome(source_id="rdap", source_name="RDAP", status="error", error=f"RDAP HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="rdap", source_name="RDAP", status="error", error="RDAP response was not JSON")
    if not isinstance(payload, dict):
        return SourceOutcome(source_id="rdap", source_name="RDAP", status="error", error="RDAP response was not a JSON object")
    return SourceOutcome(source_id="rdap", source_name="RDAP", status="ok", findings=parse_rdap_payload(domain, payload))


def parse_crtsh(domain: str, payload) -> list[Finding]:
    if not isinstance(payload, list):
        return []
    names: dict[str, dict] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        raw_names = str(row.get("name_value") or row.get("common_name") or "")
        for part in raw_names.splitlines():
            name = part.strip().lower().lstrip("*.")
            if not name or name in names:
                continue
            names[name] = {
                "issuer": row.get("issuer_name"),
                "not_before": row.get("not_before"),
                "not_after": row.get("not_after"),
            }
            if len(names) >= 25:
                break
        if len(names) >= 25:
            break
    findings = []
    for name, meta in names.items():
        links = []
        if name == domain or name.endswith("." + domain):
            links.append({
                "relation": "certificate_names",
                "target_type": "domain",
                "target_value": name,
                "evidence": f"Certificate transparency name {name}",
            })
        findings.append(
            Finding(
                entity_type="certificate",
                value=name,
                normalized_value=name,
                title="Certificate name",
                summary=f"crt.sh lists {name} in certificate transparency" + (f", issuer {meta['issuer']}." if meta.get("issuer") else "."),
                source_id="crtsh",
                source_name="crt.sh",
                source_url=f"https://crt.sh/?q={quote(domain)}",
                confidence=0.85,
                verified=True,
                kind="fact",
                attributes={**meta, "links": links},
            )
        )
    return findings


def crtsh_domain(domain: str, client=None) -> SourceOutcome:
    client = client or default_client()
    url = "https://crt.sh/"
    try:
        response = client.get(url, params={"q": domain, "output": "json"}, headers={"User-Agent": USER_AGENT}, timeout=15)
    except Exception as exc:
        return SourceOutcome(source_id="crtsh", source_name="crt.sh", status="error", error=_truncate(f"{type(exc).__name__}: {exc}"))
    if response.status_code >= 400:
        return SourceOutcome(source_id="crtsh", source_name="crt.sh", status="error", error=f"crt.sh HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="crtsh", source_name="crt.sh", status="error", error="crt.sh response was not JSON")
    findings = parse_crtsh(domain, payload)
    if not findings:
        findings.append(
            Finding(
                entity_type="domain",
                value=domain,
                normalized_value=domain,
                title="Certificate transparency",
                summary=f"crt.sh returned no certificate names for {domain}.",
                source_id="crtsh",
                source_name="crt.sh",
                source_url=f"https://crt.sh/?q={quote(domain)}",
                confidence=0.6,
                verified=True,
                kind="fact",
            )
        )
    return SourceOutcome(source_id="crtsh", source_name="crt.sh", status="ok", findings=findings)


def ripestat_prefix(ip: str, client=None) -> SourceOutcome:
    client = client or default_client()
    url = "https://stat.ripe.net/data/prefix-overview/data.json"
    try:
        response = client.get(url, params={"resource": ip}, headers={"User-Agent": USER_AGENT}, timeout=10)
    except Exception as exc:
        return SourceOutcome(source_id="ripestat", source_name="RIPEstat", status="error", error=_truncate(str(exc)))
    if response.status_code >= 400:
        return SourceOutcome(source_id="ripestat", source_name="RIPEstat", status="error", error=f"RIPEstat HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="ripestat", source_name="RIPEstat", status="error", error="RIPEstat response was not JSON")
    if payload.get("status") != "ok":
        return SourceOutcome(source_id="ripestat", source_name="RIPEstat", status="error", error=f"RIPEstat status {payload.get('status')}")
    data = payload.get("data") or {}
    findings = []
    for asn_row in data.get("asns") or []:
        asn = asn_row.get("asn")
        holder = asn_row.get("holder")
        if asn is None:
            continue
        label = f"AS{asn}"
        summary = f"RIPEstat associates {ip} with {label}" + (f" ({holder})" if holder else "") + ". This is network registration, not a device or a person."
        findings.append(
            Finding(
                entity_type="asn",
                value=label,
                normalized_value=label,
                title="RIPEstat ASN",
                summary=summary,
                source_id="ripestat",
                source_name="RIPEstat",
                source_url=f"https://stat.ripe.net/app/launchpad/{quote(ip)}",
                confidence=0.85,
                verified=True,
                kind="fact",
                attributes={
                    "asn": asn,
                    "holder": holder,
                    "prefix": data.get("resource") or data.get("block"),
                    "device_location": False,
                    "links": [{"relation": "has_asn", "target_type": "asn", "target_value": label, "evidence": summary}],
                },
            )
        )
    if not findings:
        return SourceOutcome(source_id="ripestat", source_name="RIPEstat", status="not_found", message="RIPEstat returned no ASN for this resource")
    return SourceOutcome(source_id="ripestat", source_name="RIPEstat", status="ok", findings=findings)


def github_user(username: str, client=None) -> SourceOutcome:
    client = client or default_client()
    url = f"https://api.github.com/users/{quote(username)}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    try:
        response = client.get(url, headers=headers, timeout=10)
    except Exception as exc:
        return SourceOutcome(source_id="github", source_name="GitHub public API", status="error", error=_truncate(str(exc)))
    if response.status_code == 404:
        return SourceOutcome(
            source_id="github",
            source_name="GitHub public API",
            status="not_found",
            findings=[
                Finding(
                    entity_type="username",
                    value=username,
                    normalized_value=username.lower(),
                    title="GitHub",
                    summary=f"GitHub reports no public user with the login {username}.",
                    source_id="github",
                    source_name="GitHub public API",
                    source_url=url,
                    confidence=0.95,
                    verified=True,
                    kind="fact",
                )
            ],
        )
    if response.status_code == 403:
        return SourceOutcome(source_id="github", source_name="GitHub public API", status="error", error="GitHub rate limit or access denial")
    if response.status_code >= 400:
        return SourceOutcome(source_id="github", source_name="GitHub public API", status="error", error=f"GitHub HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="github", source_name="GitHub public API", status="error", error="GitHub response was not JSON")
    login = payload.get("login") or username
    html_url = payload.get("html_url") or f"https://github.com/{login}"
    published = {key: payload.get(key) for key in ("name", "company", "blog", "location", "bio") if payload.get(key)}
    summary = f"GitHub has a public profile for {login}."
    if published.get("name"):
        summary += f" The profile publishes the display name {published['name']}, which is self-published and not an identity check."
    return SourceOutcome(
        source_id="github",
        source_name="GitHub public API",
        status="ok",
        findings=[
            Finding(
                entity_type="social_profile",
                value=html_url,
                normalized_value=login.lower(),
                title="GitHub profile",
                summary=summary,
                source_id="github",
                source_name="GitHub public API",
                source_url=html_url,
                confidence=0.95,
                verified=True,
                kind="fact",
                attributes={
                    "login": login,
                    "id": payload.get("id"),
                    "created_at": payload.get("created_at"),
                    "public_repos": payload.get("public_repos"),
                    "self_published": published,
                    "links": [{"relation": "public_account", "target_type": "social_profile", "target_value": html_url, "evidence": f"GitHub API returned login {login}"}],
                },
            )
        ],
    )


def gitlab_user(username: str, client=None) -> SourceOutcome:
    client = client or default_client()
    url = "https://gitlab.com/api/v4/users"
    try:
        response = client.get(url, params={"username": username}, headers={"User-Agent": USER_AGENT}, timeout=10)
    except Exception as exc:
        return SourceOutcome(source_id="gitlab", source_name="GitLab public API", status="error", error=_truncate(str(exc)))
    if response.status_code >= 400:
        return SourceOutcome(source_id="gitlab", source_name="GitLab public API", status="error", error=f"GitLab HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="gitlab", source_name="GitLab public API", status="error", error="GitLab response was not JSON")
    if not payload:
        return SourceOutcome(
            source_id="gitlab",
            source_name="GitLab public API",
            status="not_found",
            findings=[
                Finding(
                    entity_type="username",
                    value=username,
                    normalized_value=username.lower(),
                    title="GitLab",
                    summary=f"GitLab reports no public user with the username {username}.",
                    source_id="gitlab",
                    source_name="GitLab public API",
                    source_url=url,
                    confidence=0.9,
                    verified=True,
                    kind="fact",
                )
            ],
        )
    row = payload[0] if isinstance(payload, list) else payload
    login = row.get("username") or username
    web = row.get("web_url") or f"https://gitlab.com/{login}"
    return SourceOutcome(
        source_id="gitlab",
        source_name="GitLab public API",
        status="ok",
        findings=[
            Finding(
                entity_type="social_profile",
                value=web,
                normalized_value=login.lower(),
                title="GitLab profile",
                summary=f"GitLab has a public profile for {login}.",
                source_id="gitlab",
                source_name="GitLab public API",
                source_url=web,
                confidence=0.9,
                verified=True,
                kind="fact",
                attributes={
                    "username": login,
                    "name": row.get("name"),
                    "links": [{"relation": "public_account", "target_type": "social_profile", "target_value": web, "evidence": f"GitLab API returned username {login}"}],
                },
            )
        ],
    )


HANDLE_TEMPLATES = (
    ("reddit", "https://www.reddit.com/user/{u}"),
    ("youtube", "https://www.youtube.com/@{u}"),
    ("medium", "https://medium.com/@{u}"),
    ("keybase", "https://keybase.io/{u}"),
    ("telegram", "https://t.me/{u}"),
)


def unverified_handle_templates(username: str) -> list[Finding]:
    findings = []
    for platform, template in HANDLE_TEMPLATES:
        url = template.format(u=username)
        findings.append(
            Finding(
                entity_type="reference",
                value=url,
                normalized_value=url.lower(),
                title=f"Unverified {platform} URL",
                summary=f"Unverified public URL template for {platform}. Existence was not checked.",
                source_id="local_normalizer",
                source_name="URL template",
                source_url=None,
                confidence=0.0,
                verified=False,
                kind="reference",
                attributes={"existence": "not_checked", "live_query": False, "platform": platform},
            )
        )
    return findings


def gravatar_exists(email: str, client=None) -> SourceOutcome:
    digest = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    url = f"https://www.gravatar.com/avatar/{digest}?d=404"
    client = client or default_client()
    try:
        response = client.head(url, headers={"User-Agent": USER_AGENT}, timeout=8, follow_redirects=True)
    except Exception as exc:
        return SourceOutcome(source_id="gravatar", source_name="Gravatar", status="error", error=_truncate(str(exc)))
    if response.status_code == 200:
        summary = "A Gravatar image is published for this email hash."
        verified_exists = True
    elif response.status_code == 404:
        summary = "Gravatar has no image for this email hash."
        verified_exists = False
    else:
        return SourceOutcome(source_id="gravatar", source_name="Gravatar", status="error", error=f"Gravatar HTTP {response.status_code}")
    return SourceOutcome(
        source_id="gravatar",
        source_name="Gravatar",
        status="ok",
        findings=[
            Finding(
                entity_type="email",
                value=email,
                normalized_value=email.lower(),
                title="Gravatar",
                summary=summary,
                source_id="gravatar",
                source_name="Gravatar",
                source_url="https://gravatar.com",
                confidence=0.8,
                verified=True,
                kind="fact",
                attributes={"gravatar_present": verified_exists, "profile_scraped": False},
            )
        ],
    )


def parse_urlhaus(host: str, payload: dict) -> SourceOutcome:
    status = payload.get("query_status")
    if status == "no_results":
        return SourceOutcome(
            source_id="urlhaus",
            source_name="URLhaus",
            status="not_found",
            findings=[
                Finding(
                    entity_type="host",
                    value=host,
                    normalized_value=host.lower(),
                    title="URLhaus",
                    summary=f"URLhaus returned no current listings for {host}. Absence of a listing is not a safety guarantee.",
                    source_id="urlhaus",
                    source_name="URLhaus",
                    source_url="https://urlhaus.abuse.ch/",
                    confidence=0.75,
                    verified=True,
                    kind="fact",
                )
            ],
        )
    if status != "ok":
        return SourceOutcome(source_id="urlhaus", source_name="URLhaus", status="error", error=f"URLhaus query_status {status}")
    urls = payload.get("urls") or []
    online = [row for row in urls if str(row.get("url_status", "")).lower() == "online"]
    sample = []
    for row in urls[:10]:
        sample.append({"url": row.get("url"), "status": row.get("url_status"), "threat": row.get("threat")})
    summary = (
        f"URLhaus lists {host} in a malware URL collection ({len(urls)} URLs, {len(online)} marked online). "
        "This is an infrastructure indicator, not an accusation against a person."
    )
    return SourceOutcome(
        source_id="urlhaus",
        source_name="URLhaus",
        status="ok",
        findings=[
            Finding(
                entity_type="host",
                value=host,
                normalized_value=host.lower(),
                title="URLhaus listing",
                summary=summary,
                source_id="urlhaus",
                source_name="URLhaus",
                source_url=payload.get("urlhaus_reference") or "https://urlhaus.abuse.ch/",
                confidence=0.8,
                verified=True,
                kind="fact",
                attributes={"url_count": len(urls), "online_count": len(online), "sample": sample},
            )
        ],
    )


def urlhaus_host(host: str, client=None) -> SourceOutcome:
    client = client or default_client()
    try:
        response = client.post(
            "https://urlhaus-api.abuse.ch/v1/host/",
            data={"host": host},
            headers={"User-Agent": USER_AGENT},
            timeout=12,
        )
    except Exception as exc:
        return SourceOutcome(source_id="urlhaus", source_name="URLhaus", status="error", error=_truncate(str(exc)))
    if response.status_code >= 400:
        return SourceOutcome(source_id="urlhaus", source_name="URLhaus", status="error", error=f"URLhaus HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="urlhaus", source_name="URLhaus", status="error", error="URLhaus response was not JSON")
    return parse_urlhaus(host, payload)


def hibp_email(email: str, client=None) -> SourceOutcome:
    if not settings.hibp_api_key:
        return SourceOutcome(
            source_id="hibp",
            source_name="Have I Been Pwned",
            status="unavailable",
            required_env=["HIBP_API_KEY"],
            message="HIBP_API_KEY is not configured. No breach data was requested or invented.",
        )
    client = client or default_client()
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email)}"
    headers = {"hibp-api-key": settings.hibp_api_key, "User-Agent": USER_AGENT}
    try:
        response = client.get(url, params={"truncateResponse": "false"}, headers=headers, timeout=12)
    except Exception as exc:
        return SourceOutcome(source_id="hibp", source_name="Have I Been Pwned", status="error", error=_truncate(str(exc)))
    if response.status_code == 404:
        return SourceOutcome(
            source_id="hibp",
            source_name="Have I Been Pwned",
            status="not_found",
            findings=[
                Finding(
                    entity_type="email",
                    value=email,
                    normalized_value=email.lower(),
                    title="HIBP",
                    summary="Have I Been Pwned returned no public breach for this email. That is not a guarantee the mailbox is safe.",
                    source_id="hibp",
                    source_name="Have I Been Pwned",
                    source_url="https://haveibeenpwned.com",
                    confidence=0.8,
                    verified=True,
                    kind="fact",
                )
            ],
        )
    if response.status_code >= 400:
        return SourceOutcome(source_id="hibp", source_name="Have I Been Pwned", status="error", error=f"HIBP HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="hibp", source_name="Have I Been Pwned", status="error", error="HIBP response was not JSON")
    names = [row.get("Name") for row in payload if isinstance(row, dict) and row.get("Name")]
    return SourceOutcome(
        source_id="hibp",
        source_name="Have I Been Pwned",
        status="ok",
        findings=[
            Finding(
                entity_type="email",
                value=email,
                normalized_value=email.lower(),
                title="HIBP breaches",
                summary=f"Have I Been Pwned lists {len(names)} breach name(s) for this email: {', '.join(names[:12])}.",
                source_id="hibp",
                source_name="Have I Been Pwned",
                source_url="https://haveibeenpwned.com",
                confidence=0.85,
                verified=True,
                kind="fact",
                attributes={"breach_names": names},
            )
        ],
    )


def virustotal_indicator(kind: str, value: str, client=None) -> SourceOutcome:
    if not settings.virustotal_api_key:
        return SourceOutcome(
            source_id="virustotal",
            source_name="VirusTotal",
            status="unavailable",
            required_env=["VIRUSTOTAL_API_KEY"],
            message="VIRUSTOTAL_API_KEY is not configured. No vendor score was invented.",
        )
    path = {"ip": "ip_addresses", "domain": "domains", "hash": "files"}.get(kind)
    if not path:
        return SourceOutcome(source_id="virustotal", source_name="VirusTotal", status="error", error="Unsupported VirusTotal indicator")
    client = client or default_client()
    url = f"https://www.virustotal.com/api/v3/{path}/{quote(value)}"
    try:
        response = client.get(url, headers={"x-apikey": settings.virustotal_api_key, "User-Agent": USER_AGENT}, timeout=15)
    except Exception as exc:
        return SourceOutcome(source_id="virustotal", source_name="VirusTotal", status="error", error=_truncate(str(exc)))
    if response.status_code == 404:
        return SourceOutcome(source_id="virustotal", source_name="VirusTotal", status="not_found", message="VirusTotal has no object for this indicator")
    if response.status_code >= 400:
        return SourceOutcome(source_id="virustotal", source_name="VirusTotal", status="error", error=f"VirusTotal HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="virustotal", source_name="VirusTotal", status="error", error="VirusTotal response was not JSON")
    stats = ((payload.get("data") or {}).get("attributes") or {}).get("last_analysis_stats") or {}
    summary = (
        "VirusTotal last_analysis_stats reports "
        + ", ".join(f"{key}={stats[key]}" for key in sorted(stats))
        + ". This is a vendor-aggregate indicator, not a determination of a person's conduct."
    )
    return SourceOutcome(
        source_id="virustotal",
        source_name="VirusTotal",
        status="ok",
        findings=[
            Finding(
                entity_type=kind,
                value=value,
                normalized_value=value.lower(),
                title="VirusTotal stats",
                summary=summary,
                source_id="virustotal",
                source_name="VirusTotal",
                source_url="https://www.virustotal.com",
                confidence=0.7,
                verified=True,
                kind="fact",
                attributes={"last_analysis_stats": stats},
            )
        ],
    )


def otx_indicator(kind: str, value: str, client=None) -> SourceOutcome:
    if not settings.otx_api_key:
        return SourceOutcome(
            source_id="otx",
            source_name="AlienVault OTX",
            status="unavailable",
            required_env=["OTX_API_KEY"],
            message="OTX_API_KEY is not configured. No pulse data was invented.",
        )
    section = {"ip": "IPv4", "domain": "domain", "hash": "file"}.get(kind)
    if not section:
        return SourceOutcome(source_id="otx", source_name="AlienVault OTX", status="error", error="Unsupported OTX indicator")
    client = client or default_client()
    url = f"https://otx.alienvault.com/api/v1/indicators/{section}/{quote(value)}/general"
    try:
        response = client.get(url, headers={"X-OTX-API-KEY": settings.otx_api_key, "User-Agent": USER_AGENT}, timeout=12)
    except Exception as exc:
        return SourceOutcome(source_id="otx", source_name="AlienVault OTX", status="error", error=_truncate(str(exc)))
    if response.status_code >= 400:
        return SourceOutcome(source_id="otx", source_name="AlienVault OTX", status="error", error=f"OTX HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="otx", source_name="AlienVault OTX", status="error", error="OTX response was not JSON")
    pulses = ((payload.get("pulse_info") or {}).get("pulses")) or []
    names = [pulse.get("name") for pulse in pulses if isinstance(pulse, dict) and pulse.get("name")][:5]
    summary = f"AlienVault OTX reports {len(pulses)} pulse(s) for this indicator."
    if names:
        summary += " Named pulses include " + ", ".join(names) + "."
    summary += " This is an infrastructure feed, not an accusation against a person."
    return SourceOutcome(
        source_id="otx",
        source_name="AlienVault OTX",
        status="ok",
        findings=[
            Finding(
                entity_type=kind,
                value=value,
                normalized_value=value.lower(),
                title="OTX pulses",
                summary=summary,
                source_id="otx",
                source_name="AlienVault OTX",
                source_url="https://otx.alienvault.com",
                confidence=0.65,
                verified=True,
                kind="fact",
                attributes={"pulse_count": len(pulses), "pulse_names": names},
            )
        ],
    )


def authorized_identity(identifier: str, purpose: str, case_id: str | None, client=None) -> SourceOutcome:
    url = settings.authorized_identity_provider_url
    token = settings.authorized_identity_provider_token
    if not url or not token:
        return SourceOutcome(
            source_id="authorized_identity",
            source_name="Authorized identity provider",
            status="unavailable",
            required_env=["AUTHORIZED_IDENTITY_PROVIDER_URL", "AUTHORIZED_IDENTITY_PROVIDER_TOKEN"],
            message="No authorized identity provider is configured. NADRA and other private identity registries are not queried.",
        )
    if not url.lower().startswith("https://"):
        return SourceOutcome(
            source_id="authorized_identity",
            source_name="Authorized identity provider",
            status="unavailable",
            message="AUTHORIZED_IDENTITY_PROVIDER_URL must be HTTPS. The provider was not called.",
            required_env=["AUTHORIZED_IDENTITY_PROVIDER_URL"],
        )
    client = client or default_client()
    try:
        response = client.post(
            url,
            json={"identifier": identifier, "identifier_type": "cnic", "purpose": purpose, "case_id": case_id},
            headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
            timeout=10,
            follow_redirects=False,
        )
    except Exception as exc:
        return SourceOutcome(source_id="authorized_identity", source_name="Authorized identity provider", status="error", error=_truncate(str(exc)))
    if response.status_code >= 400:
        return SourceOutcome(source_id="authorized_identity", source_name="Authorized identity provider", status="error", error=f"Provider HTTP {response.status_code}")
    try:
        payload = response.json()
    except Exception:
        return SourceOutcome(source_id="authorized_identity", source_name="Authorized identity provider", status="error", error="Provider response was not JSON")
    if not isinstance(payload, dict):
        return SourceOutcome(source_id="authorized_identity", source_name="Authorized identity provider", status="error", error="Provider response was not a JSON object")
    return SourceOutcome(
        source_id="authorized_identity",
        source_name="Authorized identity provider",
        status="ok",
        message="Provider responded. The payload is returned to the analyst and is not written to the findings table.",
        findings=[],
        details={"payload": payload, "stored_at_rest": False},
    )


def provider_payload_for_response(outcome: SourceOutcome, payload: dict | None = None) -> dict | None:
    if outcome.status != "ok" or payload is None:
        return None
    return {
        "source_id": "authorized_identity",
        "stored_at_rest": False,
        "payload": payload,
        "note": "Returned by the operator-configured provider. Infinity X did not add identity data of its own.",
    }
