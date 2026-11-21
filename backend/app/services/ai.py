from __future__ import annotations

from app.security import DISCLAIMER

BANNED_WORDS = (
    "guilty",
    "criminal",
    "terrorist",
    "murderer",
    "fraudster",
    "pedophile",
    "offender",
    "culprit",
    "perpetrator",
    "is a scammer",
)


def _safe(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in BANNED_WORDS):
        return "A generated sentence was removed because it did not meet the language policy."
    return text


def _facts(findings: list[dict]) -> list[dict]:
    return [item for item in findings if item.get("kind") == "fact" and item.get("verified")]


def build_hypotheses(facts: list[dict]) -> list[dict]:
    hypotheses = []
    for fact in facts:
        title = fact.get("title") or ""
        blob = f"{fact.get('summary', '')} {fact.get('value', '')} {fact.get('normalized_value', '')}".lower()
        if title == "MX" and any(token in blob for token in ("google", "googlemail", "aspmx")):
            hypotheses.append({
                "kind": "hypothesis",
                "confidence": 0.3,
                "based_on": title,
                "statement": _safe(
                    f"Hypothesis: the published MX host is consistent with Google mail routing. "
                    f"This does not identify a mailbox owner and is not a finding about a person. Source value: {fact.get('value')}."
                ),
            })
        if title == "MX" and any(token in blob for token in ("outlook", "protection.outlook")):
            hypotheses.append({
                "kind": "hypothesis",
                "confidence": 0.3,
                "based_on": title,
                "statement": _safe(
                    "Hypothesis: the published MX host is consistent with Microsoft 365 mail routing. "
                    "This does not identify a mailbox owner and is not a finding about a person."
                ),
            })
        if title in {"ASN", "RIPEstat ASN"}:
            hypotheses.append({
                "kind": "hypothesis",
                "confidence": 0.25,
                "based_on": title,
                "statement": _safe(
                    f"Hypothesis: this address is announced by {fact.get('value')}. "
                    "This is network routing, not a device or a person."
                ),
            })
        if title == "Certificate name":
            hypotheses.append({
                "kind": "hypothesis",
                "confidence": 0.2,
                "based_on": title,
                "statement": _safe(
                    f"Hypothesis: certificate transparency shows the hostname {fact.get('value')} was logged. "
                    "Presence in a log is not proof the service is still online and is not an identity."
                ),
            })
    # Cap repeated certificate hypotheses.
    seen = set()
    unique = []
    for item in hypotheses:
        key = item["statement"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:12]


def build_contradictions(facts: list[dict]) -> list[dict]:
    contradictions = []
    nx = any("nxdomain" in (fact.get("summary") or "").lower() for fact in facts)
    registered = any(
        fact.get("source_id") == "rdap" and "event" in (fact.get("title") or "").lower()
        for fact in facts
    ) or any(fact.get("source_id") == "rdap" and "status" in (fact.get("title") or "").lower() for fact in facts)
    if nx and registered:
        contradictions.append({
            "statement": "DNS returned NXDOMAIN while RDAP returned registration data. Both observations are kept; neither is discarded.",
            "fact_titles": ["DNS NXDOMAIN", "RDAP"],
        })
    spf_hardfail = any(fact.get("title") == "SPF" and "-all" in (fact.get("value") or "").lower() for fact in facts)
    no_mx = any(fact.get("title") == "MX" and "no mx" in (fact.get("summary") or "").lower() for fact in facts)
    if spf_hardfail and no_mx:
        contradictions.append({
            "statement": "SPF ends with -all but no MX was published. Mail policy and mail routing look inconsistent. This is a configuration observation, not an accusation.",
            "fact_titles": ["SPF", "MX"],
        })
    return contradictions


def suggest_next_sources(facts: list[dict], unavailable: list[dict]) -> list[str]:
    suggestions = []
    unavailable_ids = {item.get("source_id") for item in unavailable}
    types = {fact.get("entity_type") for fact in facts}
    titles = {fact.get("title") for fact in facts}
    if "hibp" in unavailable_ids or ("email" in types and "HIBP" not in titles and "HIBP breaches" not in titles):
        if "hibp" in unavailable_ids:
            suggestions.append("Configure HIBP_API_KEY to query Have I Been Pwned under your license. No breach result is available until then.")
    if "virustotal" in unavailable_ids:
        suggestions.append("Configure VIRUSTOTAL_API_KEY to request VirusTotal analysis stats. No score was inferred.")
    if "otx" in unavailable_ids:
        suggestions.append("Configure OTX_API_KEY to request AlienVault OTX pulses. No pulse count was inferred.")
    if "authorized_identity" in unavailable_ids:
        suggestions.append("An authorized identity provider is not configured. Do not use NADRA or an unauthorized people-search database.")
    if any(item.get("source_id") == "crtsh" for item in unavailable) or any(
        "crt.sh" in (item.get("message") or "") for item in []
    ):
        suggestions.append("Retry certificate transparency when crt.sh is reachable.")
    error_sources = {item.get("source_id") for item in unavailable}
    if "crtsh" in error_sources:
        suggestions.append("Retry certificate transparency when crt.sh is reachable.")
    if not any(fact.get("source_id") in {"team_cymru", "ripestat"} for fact in facts) and "ip" in types:
        suggestions.append("Retry Team Cymru or RIPEstat for public ASN data if those sources errored.")
    suggestions.append("Stay on public sources and providers your organization is licensed to use.")
    cleaned = []
    for line in suggestions:
        if "subscriber" in line.lower() and "not" not in line.lower():
            continue
        cleaned.append(_safe(line))
    return cleaned


def analyze(findings: list[dict], unavailable: list[dict] | None = None) -> dict:
    unavailable = unavailable or []
    facts = _facts(findings)
    references = [item for item in findings if item.get("kind") == "reference"]
    hypotheses = build_hypotheses(facts)
    contradictions = build_contradictions(facts)
    timeline = sorted(facts, key=lambda item: item.get("collected_at") or "")
    next_sources = suggest_next_sources(facts, unavailable)
    return {
        "facts": [
            {
                "title": fact.get("title"),
                "summary": fact.get("summary"),
                "source_id": fact.get("source_id"),
                "source_name": fact.get("source_name"),
                "collected_at": fact.get("collected_at"),
                "confidence": fact.get("confidence"),
                "kind": "fact",
            }
            for fact in facts
        ],
        "references": [
            {"title": item.get("title"), "summary": item.get("summary"), "kind": "reference", "verified": False}
            for item in references
        ],
        "hypotheses": hypotheses,
        "contradictions": contradictions,
        "timeline": [
            {"collected_at": item.get("collected_at"), "title": item.get("title"), "source_id": item.get("source_id")}
            for item in timeline
        ],
        "next_sources": next_sources,
        "disclaimer": DISCLAIMER,
        "accuses_person": False,
    }
