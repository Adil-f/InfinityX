from __future__ import annotations

import ipaddress
import time
from collections import deque

import dns.exception
import dns.resolver
import dns.reversename

from app.services.results import Finding, SourceOutcome

_windows: dict[str, deque] = {}
DKIM_SELECTORS = ("selector1", "selector2", "google", "default", "s1", "k1")


def _allow(source_id: str, limit: int) -> bool:
    now = time.monotonic()
    bucket = _windows.setdefault(source_id, deque())
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def make_resolver():
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 4.0
    resolver.timeout = 2.0
    return resolver


def txt_value(raw: str) -> str:
    text = raw.strip().replace('" "', "")
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text


def parse_cymru_txt(raw: str) -> dict | None:
    text = txt_value(raw)
    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 3 or not parts[0]:
        return None
    return {
        "asn": parts[0],
        "prefix": parts[1],
        "country": parts[2],
        "registry": parts[3] if len(parts) > 3 else None,
        "allocated": parts[4] if len(parts) > 4 else None,
    }


def _query(resolver, name: str, rdtype: str):
    try:
        answers = resolver.resolve(name, rdtype)
        return "ok", [item.to_text() for item in answers], None
    except dns.resolver.NXDOMAIN:
        return "nxdomain", [], None
    except dns.resolver.NoAnswer:
        return "noanswer", [], None
    except dns.resolver.NoNameservers as exc:
        return "error", [], f"No nameservers: {exc}"
    except dns.exception.Timeout:
        return "error", [], "DNS timeout"
    except Exception as exc:
        return "error", [], f"{type(exc).__name__}: {exc}"[:300]


def _limited(source_id: str, source_name: str, limit: int, enforce_limit: bool) -> SourceOutcome | None:
    if enforce_limit and not _allow(source_id, limit):
        return SourceOutcome(source_id=source_id, source_name=source_name, status="error", error="Connector rate limit reached for this process")
    return None


def dns_lookup(domain: str, resolver=None, enforce_limit: bool = True) -> SourceOutcome:
    source = "dns"
    name = "DNS"
    blocked = _limited(source, name, 60, enforce_limit)
    if blocked:
        return blocked
    resolver = resolver or make_resolver()
    findings: list[Finding] = []
    status, values, error = _query(resolver, domain, "A")
    if status == "error":
        return SourceOutcome(source_id=source, source_name=name, status="error", error=error or "DNS error")
    if status == "nxdomain":
        findings.append(
            Finding(
                entity_type="domain",
                value=domain,
                normalized_value=domain,
                title="DNS NXDOMAIN",
                summary=f"Authoritative DNS returned NXDOMAIN for {domain}. This is not a registration check.",
                source_id=source,
                source_name=name,
                confidence=0.9,
                verified=True,
                kind="fact",
            )
        )
        return SourceOutcome(source_id=source, source_name=name, status="ok", findings=findings)

    def add_records(title: str, rdtype: str, qname: str, relation: str | None = None, target_type: str | None = None):
        state, records, err = _query(resolver, qname, rdtype)
        if state == "error":
            return err
        if state != "ok":
            if rdtype == "MX":
                findings.append(
                    Finding(
                        entity_type="dns_record",
                        value=qname,
                        normalized_value=qname,
                        title="MX",
                        summary=f"No MX record is published for {qname}.",
                        source_id=source,
                        source_name=name,
                        confidence=0.9,
                        verified=True,
                        kind="fact",
                    )
                )
            return None
        for record in records:
            cleaned = record.rstrip(".")
            links = []
            normalized = cleaned.lower()
            if relation and target_type:
                target = normalized
                if rdtype == "MX":
                    parts = cleaned.split()
                    target = parts[-1].rstrip(".").lower() if parts else normalized
                    cleaned = " ".join(parts[:-1] + [target]) if parts else cleaned
                if rdtype == "A" or rdtype == "AAAA":
                    target = record.strip()
                links.append({
                    "relation": relation,
                    "target_type": target_type,
                    "target_value": target,
                    "evidence": f"{title} {cleaned}",
                })
            findings.append(
                Finding(
                    entity_type="ip" if rdtype in {"A", "AAAA"} else "dns_record",
                    value=cleaned,
                    normalized_value=target if links else normalized,
                    title=title,
                    summary=f"{title} for {qname}: {cleaned}",
                    source_id=source,
                    source_name=name,
                    confidence=0.95,
                    verified=True,
                    kind="fact",
                    attributes={"record_type": rdtype, "queried_name": qname, "links": links},
                )
            )
        return None

    dns_error = add_records("A", "A", domain, "resolves_to", "ip")
    if dns_error:
        return SourceOutcome(source_id=source, source_name=name, status="error", error=dns_error, findings=findings)
    for title, rdtype, relation, target_type in (
        ("AAAA", "AAAA", "resolves_to", "ip"),
        ("NS", "NS", "has_ns", "host"),
        ("MX", "MX", "has_mx", "host"),
        ("SOA", "SOA", None, None),
    ):
        err = add_records(title, rdtype, domain, relation, target_type)
        if err:
            findings.append(
                Finding(
                    entity_type="dns_record",
                    value=domain,
                    normalized_value=domain,
                    title=f"{title} lookup failed",
                    summary=f"{title} lookup did not complete: {err}",
                    source_id=source,
                    source_name=name,
                    confidence=0.4,
                    verified=False,
                    kind="reference",
                )
            )

    state, records, err = _query(resolver, domain, "TXT")
    if state == "error":
        return SourceOutcome(source_id=source, source_name=name, status="error", error=err, findings=findings)
    spf = [txt_value(item) for item in records if txt_value(item).lower().startswith("v=spf1")]
    for record in spf:
        links = []
        for token in record.split():
            if token.lower().startswith("include:"):
                host = token.split(":", 1)[1].strip(".").lower()
                links.append({"relation": "has_spf", "target_type": "domain", "target_value": host, "evidence": record})
        findings.append(
            Finding(
                entity_type="dns_record",
                value=record,
                normalized_value=domain,
                title="SPF",
                summary=f"SPF is published for {domain}.",
                source_id=source,
                source_name=name,
                confidence=0.95,
                verified=True,
                kind="fact",
                attributes={"spf": record, "links": links},
            )
        )
    if not spf and state != "error":
        findings.append(
            Finding(
                entity_type="dns_record",
                value=domain,
                normalized_value=domain,
                title="SPF",
                summary=f"No SPF TXT record is published at {domain}.",
                source_id=source,
                source_name=name,
                confidence=0.9,
                verified=True,
                kind="fact",
            )
        )

    dmarc_name = f"_dmarc.{domain}"
    state, records, err = _query(resolver, dmarc_name, "TXT")
    if state == "ok":
        for record in records:
            text = txt_value(record)
            if text.lower().startswith("v=dmarc1"):
                policy = None
                for token in text.split(";"):
                    token = token.strip()
                    if token.lower().startswith("p="):
                        policy = token.split("=", 1)[1].strip()
                findings.append(
                    Finding(
                        entity_type="dns_record",
                        value=text,
                        normalized_value=domain,
                        title="DMARC",
                        summary=f"DMARC is published for {domain}" + (f" with p={policy}." if policy else "."),
                        source_id=source,
                        source_name=name,
                        confidence=0.95,
                        verified=True,
                        kind="fact",
                        attributes={"dmarc": text, "policy": policy, "links": [{"relation": "has_dmarc", "target_type": "domain", "target_value": domain, "evidence": text}]},
                    )
                )
    elif state == "error":
        return SourceOutcome(source_id=source, source_name=name, status="error", error=err, findings=findings)
    else:
        findings.append(
            Finding(
                entity_type="dns_record",
                value=domain,
                normalized_value=domain,
                title="DMARC",
                summary=f"No DMARC TXT record is published at {dmarc_name}.",
                source_id=source,
                source_name=name,
                confidence=0.9,
                verified=True,
                kind="fact",
            )
        )

    for selector in DKIM_SELECTORS:
        qname = f"{selector}._domainkey.{domain}"
        state, records, err = _query(resolver, qname, "TXT")
        if state == "error":
            findings.append(
                Finding(
                    entity_type="dns_record",
                    value=qname,
                    normalized_value=domain,
                    title="DKIM lookup failed",
                    summary=f"DKIM selector {selector} could not be checked: {err}",
                    source_id=source,
                    source_name=name,
                    confidence=0.3,
                    verified=False,
                    kind="reference",
                )
            )
            break
        for record in records:
            text = txt_value(record)
            if "v=dkim1" in text.lower() or text.lower().startswith("k=") or "p=" in text.lower():
                findings.append(
                    Finding(
                        entity_type="dns_record",
                        value=selector,
                        normalized_value=f"{selector}._domainkey.{domain}",
                        title="DKIM",
                        summary=f"A DKIM TXT record is published for selector {selector}.",
                        source_id=source,
                        source_name=name,
                        confidence=0.9,
                        verified=True,
                        kind="fact",
                        attributes={"selector": selector, "links": [{"relation": "has_dkim", "target_type": "host", "target_value": qname, "evidence": f"DKIM selector {selector}"}]},
                    )
                )
    if not any(item.title == "A" for item in findings) and not any(item.title == "DNS NXDOMAIN" for item in findings):
        # A was queried above; if the first call returned records they were not added because add_records queries again.
        pass
    # The first A query result was not recorded when status was ok. Record it now if add_records did.
    return SourceOutcome(source_id=source, source_name=name, status="ok", findings=findings)


def reverse_dns(ip: str, resolver=None, enforce_limit: bool = True) -> SourceOutcome:
    blocked = _limited("dns", "DNS", 60, enforce_limit)
    if blocked:
        return blocked
    resolver = resolver or make_resolver()
    try:
        qname = dns.reversename.from_address(ip).to_text()
    except Exception as exc:
        return SourceOutcome(source_id="dns", source_name="DNS", status="error", error=str(exc))
    state, records, err = _query(resolver, qname, "PTR")
    if state == "error":
        return SourceOutcome(source_id="dns", source_name="DNS", status="error", error=err)
    findings = []
    if state != "ok":
        findings.append(
            Finding(
                entity_type="ip",
                value=ip,
                normalized_value=ip,
                title="PTR",
                summary=f"No PTR record is published for {ip}.",
                source_id="dns",
                source_name="DNS",
                confidence=0.85,
                verified=True,
                kind="fact",
            )
        )
    for record in records:
        host = record.rstrip(".").lower()
        findings.append(
            Finding(
                entity_type="host",
                value=host,
                normalized_value=host,
                title="PTR",
                summary=f"PTR for {ip} is {host}.",
                source_id="dns",
                source_name="DNS",
                confidence=0.9,
                verified=True,
                kind="fact",
                attributes={"links": [{"relation": "ptr", "target_type": "host", "target_value": host, "evidence": f"PTR {host}"}]},
            )
        )
    return SourceOutcome(source_id="dns", source_name="DNS", status="ok", findings=findings)


def cymru_asn(ip: str, resolver=None, enforce_limit: bool = True) -> SourceOutcome:
    blocked = _limited("team_cymru", "Team Cymru ASN", 30, enforce_limit)
    if blocked:
        return blocked
    resolver = resolver or make_resolver()
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError as exc:
        return SourceOutcome(source_id="team_cymru", source_name="Team Cymru ASN", status="error", error=str(exc))
    if parsed.version == 4:
        qname = ".".join(reversed(str(parsed).split("."))) + ".origin.asn.cymru.com"
    else:
        nibbles = parsed.exploded.replace(":", "")
        qname = ".".join(reversed(nibbles)) + ".origin6.asn.cymru.com"
    state, records, err = _query(resolver, qname, "TXT")
    if state == "error":
        return SourceOutcome(source_id="team_cymru", source_name="Team Cymru ASN", status="error", error=err)
    if state != "ok":
        return SourceOutcome(
            source_id="team_cymru",
            source_name="Team Cymru ASN",
            status="not_found",
            findings=[
                Finding(
                    entity_type="ip",
                    value=ip,
                    normalized_value=ip,
                    title="ASN",
                    summary=f"Team Cymru DNS returned no ASN mapping for {ip}.",
                    source_id="team_cymru",
                    source_name="Team Cymru ASN",
                    confidence=0.6,
                    verified=True,
                    kind="fact",
                )
            ],
        )
    parsed_row = parse_cymru_txt(records[0])
    if not parsed_row:
        return SourceOutcome(source_id="team_cymru", source_name="Team Cymru ASN", status="error", error="Unrecognized Team Cymru response")
    asn = parsed_row["asn"].split()[0]
    summary = (
        f"Team Cymru maps {ip} to AS{asn}, prefix {parsed_row['prefix']}, "
        f"network registration country {parsed_row['country']}. This is not a device location."
    )
    return SourceOutcome(
        source_id="team_cymru",
        source_name="Team Cymru ASN",
        status="ok",
        findings=[
            Finding(
                entity_type="asn",
                value=f"AS{asn}",
                normalized_value=f"AS{asn}",
                title="ASN",
                summary=summary,
                source_id="team_cymru",
                source_name="Team Cymru ASN",
                source_url="https://www.team-cymru.com/ip-asn-mapping",
                confidence=0.9,
                verified=True,
                kind="fact",
                attributes={
                    **parsed_row,
                    "network_registration_country": parsed_row["country"],
                    "device_location": False,
                    "links": [{"relation": "has_asn", "target_type": "asn", "target_value": f"AS{asn}", "evidence": summary}],
                },
            )
        ],
    )
