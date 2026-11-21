import dns.exception
import dns.resolver

from app.services.dns_source import dns_lookup, parse_cymru_txt
from app.services.http_sources import hibp_email, parse_rdap_payload, parse_urlhaus
from app.services.results import Finding, publishable


class FakeRdata:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text


class FakeResolver:
    """Development fixture resolver. These answers are not live lookups."""

    def __init__(self, mapping):
        self.mapping = mapping

    def resolve(self, name, rdtype):
        key = (str(name).lower().rstrip("."), rdtype)
        if key not in self.mapping:
            raise dns.resolver.NoAnswer()
        status, values = self.mapping[key]
        if status == "nxdomain":
            raise dns.resolver.NXDOMAIN()
        if status == "error":
            raise dns.exception.Timeout()
        return [FakeRdata(value) for value in values]


def test_cymru_parser_reads_a_fixture_string():
    parsed = parse_cymru_txt('"15169 | 8.8.8.0/24 | US | arin | 1992-12-01"')
    assert parsed["asn"] == "15169"
    assert parsed["country"] == "US"


def test_dns_orchestration_uses_fixture_answers():
    resolver = FakeResolver({
        ("example.com", "A"): ("ok", ["93.184.216.34"]),
        ("example.com", "AAAA"): ("noanswer", []),
        ("example.com", "NS"): ("ok", ["ns1.example.com."]),
        ("example.com", "MX"): ("ok", ["10 aspmx.l.google.com."]),
        ("example.com", "SOA"): ("ok", ["ns1.example.com. hostmaster.example.com. 1 7200 600 1209600 3600"]),
        ("example.com", "TXT"): ("ok", ['"v=spf1 include:_spf.example.com -all"']),
        ("_dmarc.example.com", "TXT"): ("ok", ['"v=DMARC1; p=reject"']),
        ("selector1._domainkey.example.com", "TXT"): ("ok", ['"v=DKIM1; k=rsa; p=ABC"']),
    })
    outcome = dns_lookup("example.com", resolver=resolver, enforce_limit=False)
    assert outcome.status == "ok"
    titles = {finding.title for finding in outcome.findings}
    assert {"A", "MX", "SPF", "DMARC", "DKIM", "NS"}.issubset(titles)
    mx = next(finding for finding in outcome.findings if finding.title == "MX")
    assert mx.attributes["links"][0]["relation"] == "has_mx"
    assert all(not finding.is_fixture for finding in outcome.findings)


def test_rdap_parser_extracts_registrar_and_nameserver():
    payload = {
        "ldhName": "EXAMPLE.COM",
        "status": ["active"],
        "nameservers": [{"ldhName": "A.IANA-SERVERS.NET"}],
        "events": [{"eventAction": "registration", "eventDate": "1995-08-14T04:00:00Z"}],
        "entities": [{"roles": ["registrar"], "vcardArray": ["vcard", [["fn", {}, "text", "Example Registrar"]]]}],
    }
    findings = parse_rdap_payload("example.com", payload)
    assert any(item.title == "RDAP registrar" and "Example Registrar" in item.summary for item in findings)
    assert any(item.attributes.get("links") for item in findings)


def test_urlhaus_no_results_is_not_a_clean_bill():
    outcome = parse_urlhaus("example.com", {"query_status": "no_results"})
    assert outcome.status == "not_found"
    assert "not a safety guarantee" in outcome.findings[0].summary


def test_hibp_without_a_key_does_not_invent_breaches():
    outcome = hibp_email("analyst@example.com")
    assert outcome.status == "unavailable"
    assert outcome.findings == []
    assert "HIBP_API_KEY" in outcome.required_env


def test_fixture_findings_are_not_publishable():
    finding = Finding(
        entity_type="domain",
        value="example.com",
        normalized_value="example.com",
        title="Fixture",
        summary="development fixture",
        source_id="dns",
        source_name="DNS",
        confidence=1,
        verified=True,
        kind="fact",
        is_fixture=True,
    )
    clean, blocked = publishable([finding])
    assert blocked is True
    assert clean == []
