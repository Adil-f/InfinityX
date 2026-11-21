from __future__ import annotations

"""Connector catalog. Keyed providers stay unavailable until their env vars are set."""

from app.config import Settings

CONNECTORS: list[dict] = [
    {
        "id": "numbering_plan",
        "name": "Numbering plan",
        "category": "local",
        "required_env": [],
        "rate_per_minute": 600,
        "timeout_seconds": 1,
        "description": "Offline libphonenumber metadata: format, country, number type, and prefix carrier. Not a subscriber lookup.",
    },
    {
        "id": "cnic_format",
        "name": "CNIC format",
        "category": "local",
        "required_env": [],
        "rate_per_minute": 600,
        "timeout_seconds": 1,
        "description": "Pakistani CNIC format validation only. Does not query NADRA or any identity registry.",
    },
    {
        "id": "evidence_hash",
        "name": "Evidence hashing",
        "category": "local",
        "required_env": [],
        "rate_per_minute": 120,
        "timeout_seconds": 5,
        "description": "Local SHA-256, SHA-1, and MD5 of analyst-supplied bytes. File contents are not stored or sent to a provider.",
    },
    {
        "id": "local_normalizer",
        "name": "Local normalizer",
        "category": "local",
        "required_env": [],
        "rate_per_minute": 600,
        "timeout_seconds": 1,
        "description": "Syntax checks and a short built-in list of well-known disposable mail domains. Not a live reputation feed.",
    },
    {
        "id": "dns",
        "name": "DNS",
        "category": "infrastructure",
        "required_env": [],
        "rate_per_minute": 60,
        "timeout_seconds": 4,
        "description": "Public DNS for A, AAAA, NS, MX, SOA, TXT, SPF, DMARC, DKIM presence, and PTR.",
    },
    {
        "id": "rdap",
        "name": "RDAP",
        "category": "infrastructure",
        "required_env": [],
        "rate_per_minute": 20,
        "timeout_seconds": 12,
        "description": "Public registration data via the RDAP bootstrap at rdap.org.",
    },
    {
        "id": "crtsh",
        "name": "Certificate Transparency (crt.sh)",
        "category": "infrastructure",
        "required_env": [],
        "rate_per_minute": 10,
        "timeout_seconds": 15,
        "description": "Public certificate transparency names from crt.sh.",
    },
    {
        "id": "team_cymru",
        "name": "Team Cymru ASN",
        "category": "infrastructure",
        "required_env": [],
        "rate_per_minute": 30,
        "timeout_seconds": 4,
        "description": "Public IP-to-ASN mapping over DNS (origin.asn.cymru.com). Country is network registration, not a device location.",
    },
    {
        "id": "ripestat",
        "name": "RIPEstat",
        "category": "infrastructure",
        "required_env": [],
        "rate_per_minute": 20,
        "timeout_seconds": 10,
        "description": "Public prefix and ASN holder data from stat.ripe.net.",
    },
    {
        "id": "github",
        "name": "GitHub public API",
        "category": "public_profile",
        "required_env": [],
        "optional_env": ["GITHUB_TOKEN"],
        "rate_per_minute": 20,
        "timeout_seconds": 10,
        "description": "Public GitHub user profile. GITHUB_TOKEN is optional and only raises the rate limit.",
    },
    {
        "id": "gitlab",
        "name": "GitLab public API",
        "category": "public_profile",
        "required_env": [],
        "rate_per_minute": 20,
        "timeout_seconds": 10,
        "description": "Public GitLab user lookup by username.",
    },
    {
        "id": "gravatar",
        "name": "Gravatar",
        "category": "public_profile",
        "required_env": [],
        "rate_per_minute": 30,
        "timeout_seconds": 8,
        "description": "Public avatar existence for an email hash. No profile scrape.",
    },
    {
        "id": "urlhaus",
        "name": "URLhaus",
        "category": "threat",
        "required_env": [],
        "rate_per_minute": 10,
        "timeout_seconds": 12,
        "description": "Public malware-URL host listings from abuse.ch. An empty answer is not a safety guarantee.",
    },
    {
        "id": "hibp",
        "name": "Have I Been Pwned",
        "category": "threat",
        "required_env": ["HIBP_API_KEY"],
        "rate_per_minute": 10,
        "timeout_seconds": 12,
        "description": "Breach names for an email the analyst already holds. Unavailable until HIBP_API_KEY is set. No fabricated breach list.",
    },
    {
        "id": "virustotal",
        "name": "VirusTotal",
        "category": "threat",
        "required_env": ["VIRUSTOTAL_API_KEY"],
        "rate_per_minute": 8,
        "timeout_seconds": 15,
        "description": "Vendor-aggregate analysis stats. Unavailable until VIRUSTOTAL_API_KEY is set.",
    },
    {
        "id": "otx",
        "name": "AlienVault OTX",
        "category": "threat",
        "required_env": ["OTX_API_KEY"],
        "rate_per_minute": 10,
        "timeout_seconds": 12,
        "description": "Pulse counts for an indicator. Unavailable until OTX_API_KEY is set.",
    },
    {
        "id": "authorized_identity",
        "name": "Authorized identity provider",
        "category": "identity",
        "required_env": ["AUTHORIZED_IDENTITY_PROVIDER_URL", "AUTHORIZED_IDENTITY_PROVIDER_TOKEN"],
        "rate_per_minute": 6,
        "timeout_seconds": 10,
        "description": "Operator-configured HTTPS provider. The platform does not ship a NADRA or people-search integration.",
    },
    {
        "id": "stripe",
        "name": "Stripe billing",
        "category": "billing",
        "required_env": ["STRIPE_SECRET_KEY"],
        "optional_env": ["STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_PRO", "STRIPE_PRICE_ENTERPRISE"],
        "rate_per_minute": 20,
        "timeout_seconds": 15,
        "description": "Checkout and signed webhooks. Test mode is whatever Stripe account the secret key belongs to. No charge is simulated locally.",
    },
]

ENV_TO_SETTING = {
    "HIBP_API_KEY": "hibp_api_key",
    "VIRUSTOTAL_API_KEY": "virustotal_api_key",
    "OTX_API_KEY": "otx_api_key",
    "GITHUB_TOKEN": "github_token",
    "STRIPE_SECRET_KEY": "stripe_secret_key",
    "STRIPE_WEBHOOK_SECRET": "stripe_webhook_secret",
    "STRIPE_PRICE_PRO": "stripe_price_pro",
    "STRIPE_PRICE_ENTERPRISE": "stripe_price_enterprise",
    "AUTHORIZED_IDENTITY_PROVIDER_URL": "authorized_identity_provider_url",
    "AUTHORIZED_IDENTITY_PROVIDER_TOKEN": "authorized_identity_provider_token",
}


def connector_by_id(source_id: str) -> dict | None:
    for item in CONNECTORS:
        if item["id"] == source_id:
            return item
    return None


def missing_env(spec: dict, current: Settings) -> list[str]:
    missing = []
    for name in spec.get("required_env", []):
        attr = ENV_TO_SETTING.get(name)
        value = getattr(current, attr, None) if attr else None
        if not value:
            missing.append(name)
    return missing


def configuration_status(spec: dict, current: Settings, enabled: bool = True) -> str:
    if not enabled:
        return "disabled"
    if missing_env(spec, current):
        return "unavailable"
    return "configured"
