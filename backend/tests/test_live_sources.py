"""Live public-source checks. A failure to reach a source must stay an error, not a fabricated record."""

from app.services.dns_source import cymru_asn, dns_lookup
from app.services.http_sources import crtsh_domain, rdap_domain, ripestat_prefix


def test_live_public_sources_are_honest():
    checks = {
        "dns": dns_lookup("example.com", enforce_limit=False),
        "rdap": rdap_domain("example.com"),
        "crtsh": crtsh_domain("example.com"),
        "cymru": cymru_asn("8.8.8.8", enforce_limit=False),
        "ripestat": ripestat_prefix("8.8.8.8"),
    }
    for name, outcome in checks.items():
        assert outcome.status in {"ok", "not_found", "error"}
        if outcome.status == "error":
            assert outcome.error
            assert all(not finding.verified for finding in outcome.findings) or outcome.findings == []
        elif name == "dns":
            assert any(finding.verified and finding.title in {"A", "NS", "MX", "SOA"} for finding in outcome.findings)
        elif name == "cymru" and outcome.status == "ok":
            assert outcome.findings[0].attributes.get("device_location") is False
