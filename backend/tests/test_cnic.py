from app.services.cnic import inspect_cnic


def test_cnic_format_does_not_identify_a_person():
    result = inspect_cnic("35202-1234567-1")
    finding = result.findings[0]
    assert finding.attributes["format_valid"] is True
    assert finding.attributes["identity_lookup"] is False
    assert finding.attributes["checksum_applied"] is False
    assert finding.attributes["series_region"] == "Punjab"
    assert "35202-1234567-1" not in finding.value
    assert "3520212345671" not in finding.value
    assert result.unavailable[0]["source_id"] == "authorized_identity"
    assert "not queried" in result.unavailable[0]["message"].lower()
    assert all(item.source_id != "nadra" for item in result.findings)


def test_invalid_cnic_is_a_format_result():
    result = inspect_cnic("123")
    assert result.findings[0].attributes["format_valid"] is False
    assert "123" not in result.findings[0].summary
