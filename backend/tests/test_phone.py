import json

from app.services.phone import inspect_phone

FORBIDDEN = {"subscriber_name", "person_name", "owner_name", "cnic", "imei", "imsi", "latitude", "longitude"}


def _blob(result):
    return json.dumps(result.findings[0].as_dict() if result.findings else {}) + json.dumps(result.errors) + json.dumps(result.notes)


def test_pakistan_and_italy_numbers_expose_only_numbering_metadata():
    pakistan = inspect_phone("+923001234567")
    italy = inspect_phone("+393331234567")
    assert pakistan.status == "completed"
    assert pakistan.findings[0].attributes["country_code"] == 92
    assert pakistan.findings[0].attributes["region_code"] == "PK"
    assert italy.findings[0].attributes["region_code"] == "IT"
    assert italy.findings[0].attributes["subscriber_lookup"] is False
    for result in (pakistan, italy):
        keys = set(result.findings[0].attributes)
        assert FORBIDDEN.isdisjoint(keys)
        assert "subscriber" not in _blob(result).lower() or "no subscriber" in _blob(result).lower()


def test_national_number_without_country_hint_is_rejected():
    result = inspect_phone("03001234567")
    assert result.status == "rejected"
    assert result.external_attempted is False
    assert result.findings == []


def test_region_hint_is_recorded_as_a_hint():
    result = inspect_phone("3001234567", region="PK")
    assert result.status == "completed"
    assert result.findings[0].attributes["parsing_region_hint"] == "PK"
    assert result.findings[0].attributes["subscriber_lookup"] is False
