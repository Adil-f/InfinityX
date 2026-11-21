from __future__ import annotations

import re

from app.security import identifier_hash
from app.services.results import Finding, ModuleResult, SourceOutcome, absorb

# Commonly published CNIC series prefixes. This is format geography, not a residence or an identity.
CNIC_REGION = {
    "1": "Khyber Pakhtunkhwa",
    "2": "Former FATA / merged districts",
    "3": "Punjab",
    "4": "Sindh",
    "5": "Balochistan",
    "6": "Islamabad Capital Territory",
    "7": "Gilgit-Baltistan",
}


def redact_cnic(digits: str) -> str:
    return f"{digits[0]}****-*******-{digits[-1]}"


def inspect_cnic(raw: str, provider: SourceOutcome | None = None) -> ModuleResult:
    result = ModuleResult(query_type="cnic", normalized_query="", external_attempted=False)
    result.notes.append("Format validation only. NADRA and other private identity registries are not queried by this platform.")
    digits = re.sub(r"\D", "", raw or "")
    shape_ok = bool(re.fullmatch(r"\d{13}", digits))
    if not shape_ok:
        result.normalized_query = "[invalid-format]"
        result.findings.append(
            Finding(
                entity_type="cnic",
                value="[invalid-format]",
                normalized_value="[invalid-format]",
                title="CNIC format",
                summary="The value does not match the 13-digit CNIC format. No identity registry was queried.",
                source_id="cnic_format",
                source_name="CNIC format rules",
                confidence=0.95,
                verified=True,
                kind="fact",
                attributes={"format_valid": False, "identity_lookup": False},
            )
        )
    else:
        redacted = redact_cnic(digits)
        result.normalized_query = redacted
        region = CNIC_REGION.get(digits[0])
        region_text = region or "not in the commonly published series map"
        result.findings.append(
            Finding(
                entity_type="cnic",
                value=redacted,
                normalized_value=redacted,
                title="CNIC format",
                summary=(
                    "The value matches the 13-digit CNIC format. "
                    "This does not mean a record exists and does not identify a person."
                ),
                source_id="cnic_format",
                source_name="CNIC format rules",
                confidence=0.9,
                verified=True,
                kind="fact",
                attributes={
                    "format_valid": True,
                    "series_prefix": digits[0],
                    "series_region": region_text,
                    "series_note": "Published CNIC series prefix. Not a residence lookup and not an identity.",
                    "check_digit_present": True,
                    "checksum_applied": False,
                    "identifier_sha256": identifier_hash(digits),
                    "identity_lookup": False,
                    "persisted": "redacted",
                },
            )
        )
    if provider is None:
        provider = SourceOutcome(
            source_id="authorized_identity",
            source_name="Authorized identity provider",
            status="unavailable",
            required_env=[],
            message=(
                "CNIC checks are format validation only. NADRA is not queried. "
                "AUTHORIZED_IDENTITY_PROVIDER_URL and AUTHORIZED_IDENTITY_PROVIDER_TOKEN are not used by this search."
            ),
        )
    absorb(result, provider)
    return result
