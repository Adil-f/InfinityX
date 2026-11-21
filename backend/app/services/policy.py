from __future__ import annotations

"""Graph edge policy. Identity merges are rejected; edges need evidence and a source."""

ALLOWED_RELATIONS = {
    "has_domain",
    "has_mx",
    "has_ns",
    "has_spf",
    "has_dmarc",
    "has_dkim",
    "resolves_to",
    "ptr",
    "has_asn",
    "has_registrar",
    "certificate_names",
    "public_account",
    "has_txt",
}

FORBIDDEN_RELATIONS = {
    "same_person",
    "identified_as",
    "subscriber_of",
    "owns",
    "cnic_holder",
    "located_at",
    "device_of",
    "real_name",
    "lives_at",
    "family_of",
    "phone_owner",
}

KNOWN_EDGE_SOURCES = {
    "dns",
    "rdap",
    "crtsh",
    "team_cymru",
    "ripestat",
    "github",
    "gitlab",
    "gravatar",
    "urlhaus",
    "numbering_plan",
    "local_normalizer",
    "analyst_record",
}


class PolicyError(ValueError):
    pass


def validate_edge(relation: str, evidence: str, source_id: str, confidence: float) -> float:
    if relation in FORBIDDEN_RELATIONS or relation not in ALLOWED_RELATIONS:
        raise PolicyError(
            "That relationship is not allowed. Identity merges, subscriber links, and device or location links are rejected."
        )
    if not evidence or len(evidence.strip()) < 3:
        raise PolicyError("An edge requires a short evidence statement")
    if source_id not in KNOWN_EDGE_SOURCES:
        raise PolicyError("Unknown evidence source")
    try:
        score = float(confidence)
    except (TypeError, ValueError) as exc:
        raise PolicyError("Confidence must be a number from 0 to 1") from exc
    if not 0 <= score <= 1:
        raise PolicyError("Confidence must be a number from 0 to 1")
    if source_id == "analyst_record":
        score = min(score, 0.4)
    return score
