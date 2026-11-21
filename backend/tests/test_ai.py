from app.services.ai import analyze
from app.services.reports import render_report

BANNED = ("guilty", "criminal", "terrorist", "fraudster", "offender")


def _mx():
    return {
        "kind": "fact",
        "verified": True,
        "source_id": "dns",
        "source_name": "DNS",
        "title": "MX",
        "summary": "MX for example.com: 10 aspmx.l.google.com",
        "value": "10 aspmx.l.google.com",
        "normalized_value": "aspmx.l.google.com",
        "entity_type": "dns_record",
        "collected_at": "2026-01-01T00:00:00+00:00",
        "confidence": 0.95,
        "attributes": {},
    }


def test_analysis_separates_facts_and_does_not_accuse():
    findings = [
        _mx(),
        {
            "kind": "fact",
            "verified": True,
            "source_id": "urlhaus",
            "title": "URLhaus listing",
            "summary": "URLhaus lists this host in a malware URL collection.",
            "entity_type": "domain",
            "normalized_value": "example.com",
            "collected_at": "2026-01-02T00:00:00+00:00",
            "confidence": 0.8,
            "value": "example.com",
            "attributes": {},
        },
        {
            "kind": "reference",
            "verified": False,
            "title": "Unverified reddit URL",
            "summary": "Existence was not checked.",
            "source_id": "local_normalizer",
        },
    ]
    result = analyze(findings, [{"source_id": "hibp", "message": "HIBP_API_KEY is not configured"}])
    assert result["accuses_person"] is False
    assert result["facts"][0]["kind"] == "fact"
    assert result["hypotheses"]
    assert all(item["kind"] == "hypothesis" for item in result["hypotheses"])
    prose = " ".join(item["statement"] for item in result["hypotheses"]) + result["disclaimer"] + " ".join(result["next_sources"])
    for word in BANNED:
        assert word not in prose.lower()
    assert "not a finding about a person" in prose.lower() or "not a person" in prose.lower()
    assert any("HIBP_API_KEY" in line for line in result["next_sources"])


def test_report_includes_disclaimer():
    body = render_report(
        title="Case",
        purpose="Authorized security investigation",
        lawful_basis="legitimate_interest",
        findings=[_mx()],
        unavailable=[{"source_id": "virustotal", "source_name": "VirusTotal", "message": "VIRUSTOTAL_API_KEY is not configured", "required_env": ["VIRUSTOTAL_API_KEY"]}],
    )
    assert "does not accuse" in body.lower()
    assert "aspmx.l.google.com" in body
    assert "guilty" not in body.lower()
