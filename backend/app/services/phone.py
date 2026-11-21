from __future__ import annotations

import phonenumbers
from phonenumbers import PhoneNumberType, carrier, timezone as phone_timezone

from app.services.results import Finding, ModuleResult

TYPE_NAMES = {
    PhoneNumberType.FIXED_LINE: "fixed_line",
    PhoneNumberType.MOBILE: "mobile",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
    PhoneNumberType.TOLL_FREE: "toll_free",
    PhoneNumberType.PREMIUM_RATE: "premium_rate",
    PhoneNumberType.SHARED_COST: "shared_cost",
    PhoneNumberType.VOIP: "voip",
    PhoneNumberType.PERSONAL_NUMBER: "personal_number",
    PhoneNumberType.PAGER: "pager",
    PhoneNumberType.UAN: "uan",
    PhoneNumberType.VOICEMAIL: "voicemail",
    PhoneNumberType.UNKNOWN: "unknown",
}


def inspect_phone(raw: str, region: str | None = None) -> ModuleResult:
    result = ModuleResult(query_type="phone", normalized_query=raw.strip(), external_attempted=False)
    result.notes.append("No subscriber lookup was performed. Carrier and country come from the numbering plan, not from a person.")
    text = raw.strip()
    hint = region.strip().upper() if region else None
    if hint and (len(hint) != 2 or not hint.isalpha()):
        result.status = "rejected"
        result.errors.append({"source_id": "numbering_plan", "source_name": "Numbering plan", "message": "Region hint must be a two-letter ISO country code"})
        return result
    if text.startswith("00"):
        text = "+" + text[2:]
    if not text.startswith("+") and not hint:
        result.status = "rejected"
        result.errors.append({
            "source_id": "numbering_plan",
            "source_name": "Numbering plan",
            "message": "Use international format starting with +, or select a country parsing hint. A country is not inferred from a national number.",
        })
        return result
    try:
        number = phonenumbers.parse(text, hint)
    except phonenumbers.NumberParseException as exc:
        result.status = "rejected"
        result.errors.append({"source_id": "numbering_plan", "source_name": "Numbering plan", "message": f"Could not parse the number ({exc})"})
        return result

    e164 = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    international = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    national = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.NATIONAL)
    region_code = phonenumbers.region_code_for_number(number) or hint
    number_type = TYPE_NAMES.get(phonenumbers.number_type(number), "unknown")
    valid = phonenumbers.is_valid_number(number)
    possible = phonenumbers.is_possible_number(number)
    carrier_name = carrier.name_for_number(number, "en") or None
    zones = list(phone_timezone.time_zones_for_number(number) or [])
    result.normalized_query = e164
    attributes = {
        "e164": e164,
        "international": international,
        "national": national,
        "country_code": number.country_code,
        "region_code": region_code,
        "number_type": number_type,
        "valid": valid,
        "possible": possible,
        "numbering_plan_carrier": carrier_name,
        "numbering_plan_timezones": zones,
        "parsing_region_hint": hint,
        "subscriber_lookup": False,
        "device_location": False,
    }
    summary = (
        f"{e164} is a {number_type.replace('_', ' ')} number"
        + (f" in {region_code}" if region_code else "")
        + (". It matches the numbering plan." if valid else ". It does not match the numbering plan as a valid number.")
    )
    result.findings.append(
        Finding(
            entity_type="phone",
            value=international,
            normalized_value=e164,
            title="Phone format",
            summary=summary,
            source_id="numbering_plan",
            source_name="libphonenumber numbering plan",
            confidence=0.95 if valid else 0.7,
            verified=True,
            kind="fact",
            attributes=attributes,
        )
    )
    if carrier_name:
        result.findings.append(
            Finding(
                entity_type="phone",
                value=carrier_name,
                normalized_value=e164,
                title="Numbering-plan carrier",
                summary=f"Prefix metadata names {carrier_name}. This is not the current subscriber's carrier and not a person.",
                source_id="numbering_plan",
                source_name="libphonenumber numbering plan",
                confidence=0.55,
                verified=True,
                kind="fact",
                attributes={"numbering_plan_carrier": carrier_name, "subscriber_lookup": False},
            )
        )
    else:
        result.notes.append("No numbering-plan carrier name is published for this prefix.")
    return result
