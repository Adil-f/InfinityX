import pytest

from app.services.policy import PolicyError, validate_edge


def test_identity_merge_is_rejected():
    with pytest.raises(PolicyError):
        validate_edge("same_person", "analyst hunch", "analyst_record", 0.9)


def test_evidence_link_is_allowed_and_analyst_confidence_is_capped():
    score = validate_edge("has_ns", "RDAP nameserver ns1.example.com", "rdap", 0.9)
    assert score == 0.9
    capped = validate_edge("has_mx", "Analyst recorded the MX host from a ticket", "analyst_record", 0.95)
    assert capped == 0.4
