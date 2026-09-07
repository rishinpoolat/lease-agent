from agents.rules import UnitRecord, check_r1, check_r2, check_r3, check_r4, check_r5, check_r6, check_r7, evaluate_rules
from agents.schemas import ExtractedField


def field(name: str, value, confidence: str = "high") -> ExtractedField:
    return ExtractedField(field_name=name, value=value, confidence=confidence, source_excerpt="x" if confidence != "not_found" else None)


def test_r1_pass_when_deposit_covers_month_rent():
    fields = {"deposit_amount": field("deposit_amount", 8500), "rent_amount": field("rent_amount", 8500), "rent_frequency": field("rent_frequency", "monthly")}
    result = check_r1(fields, {})
    assert result.verdict == "PASS"


def test_r1_fail_when_deposit_below_month_rent():
    fields = {"deposit_amount": field("deposit_amount", 1000), "rent_amount": field("rent_amount", 8500), "rent_frequency": field("rent_frequency", "monthly")}
    result = check_r1(fields, {})
    assert result.verdict == "FAIL"


def test_r1_not_determinable_when_deposit_missing():
    fields = {"rent_amount": field("rent_amount", 8500), "rent_frequency": field("rent_frequency", "monthly")}
    result = check_r1(fields, {})
    assert result.verdict == "NOT_DETERMINABLE"


def test_r3_fail_when_term_exceeds_36_months():
    fields = {"start_date": field("start_date", "2020-01-01"), "end_date": field("end_date", "2025-01-01")}
    result = check_r3(fields, {})
    assert result.verdict == "FAIL"


def test_r3_pass_within_36_months():
    fields = {"start_date": field("start_date", "2026-01-01"), "end_date": field("end_date", "2027-01-01")}
    assert check_r3(fields, {}).verdict == "PASS"


def test_r4_fail_when_expiry_before_commencement():
    fields = {"start_date": field("start_date", "2027-01-01"), "end_date": field("end_date", "2026-01-01")}
    assert check_r4(fields, {}).verdict == "FAIL"


def test_r4_not_determinable_when_dates_missing():
    assert check_r4({}, {}).verdict == "NOT_DETERMINABLE"


def test_r6_pass_when_annual_reconciles():
    fields = {"rent_amount": field("rent_amount", 1000), "rent_frequency": field("rent_frequency", "monthly"), "annual_rent": field("annual_rent", 12000)}
    assert check_r6(fields, {}).verdict == "PASS"


def test_r6_fail_when_annual_does_not_reconcile():
    fields = {"rent_amount": field("rent_amount", 1000), "rent_frequency": field("rent_frequency", "monthly"), "annual_rent": field("annual_rent", 999)}
    assert check_r6(fields, {}).verdict == "FAIL"


def test_r2_pass_when_mechanism_has_a_percentage():
    fields = {"escalation_clause": field("escalation_clause", {"is_defined": True, "mechanism_text": "rent increases by 5% annually"})}
    assert check_r2(fields, {}).verdict == "PASS"


def test_r2_fail_when_only_vague_language_with_no_mechanism():
    fields = {"escalation_clause": field("escalation_clause", {"is_defined": False, "mechanism_text": "as mutually agreed"})}
    assert check_r2(fields, {}).verdict == "FAIL"


def test_r2_fail_when_is_defined_explicitly_false():
    fields = {"escalation_clause": field("escalation_clause", {"is_defined": False, "mechanism_text": ""})}
    assert check_r2(fields, {}).verdict == "FAIL"


def test_r2_not_determinable_when_missing():
    assert check_r2({}, {}).verdict == "NOT_DETERMINABLE"


def test_r2_accepts_a_plain_string_value_not_just_a_dict():
    fields = {"escalation_clause": field("escalation_clause", "increases 5% each year")}
    assert check_r2(fields, {}).verdict == "PASS"


def test_r5_pass_when_both_parties_identified_and_signed():
    fields = {
        "landlord_name": field("landlord_name", "Acme"),
        "tenant_name": field("tenant_name", "Bob"),
        "landlord_signed": field("landlord_signed", True),
        "tenant_signed": field("tenant_signed", True),
    }
    assert check_r5(fields, {}).verdict == "PASS"


def test_r5_fail_when_a_party_has_not_signed():
    fields = {
        "landlord_name": field("landlord_name", "Acme"),
        "tenant_name": field("tenant_name", "Bob"),
        "landlord_signed": field("landlord_signed", True),
        "tenant_signed": field("tenant_signed", False),
    }
    assert check_r5(fields, {}).verdict == "FAIL"


def test_r5_not_determinable_when_parties_missing():
    assert check_r5({}, {}).verdict == "NOT_DETERMINABLE"


def test_r5_not_determinable_when_signatures_cannot_be_read():
    fields = {
        "landlord_name": field("landlord_name", "Acme"),
        "tenant_name": field("tenant_name", "Bob"),
    }
    assert check_r5(fields, {}).verdict == "NOT_DETERMINABLE"


def test_r7_pass_when_unit_available():
    units = {"MC-B-1204": UnitRecord(unit_id="MC-B-1204", label="Apartment 1204", status="available")}
    fields = {"unit_id": field("unit_id", "MC-B-1204")}
    assert check_r7(fields, units).verdict == "PASS"


def test_r7_fail_when_unit_occupied():
    units = {"MC-B-1205": UnitRecord(unit_id="MC-B-1205", label="Apartment 1205", status="occupied")}
    fields = {"unit_id": field("unit_id", "MC-B-1205")}
    assert check_r7(fields, units).verdict == "FAIL"


def test_r7_not_determinable_when_unit_unmatched():
    fields = {"unit_id": field("unit_id", None, confidence="not_found")}
    assert check_r7(fields, {}).verdict == "NOT_DETERMINABLE"


def test_evaluate_rules_returns_all_seven_rule_ids():
    fields = [field("rent_amount", 8500)]
    results = evaluate_rules(fields, {})
    assert {r.rule_id for r in results} == {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}
