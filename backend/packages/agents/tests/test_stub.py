from pathlib import Path

from agents.stub import StubModelProvider

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_LEASE = REPO_ROOT / "fixtures" / "sample_lease.txt"


def _fields_by_name(result):
    return {f.field_name: f for f in result.fields}


def test_extracts_core_fields_from_fixture_lease():
    text = FIXTURE_LEASE.read_text()
    result = StubModelProvider().extract_lease(text)
    fields = _fields_by_name(result)

    assert fields["landlord_name"].value == "Marina Crest Holdings W.L.L."
    assert fields["landlord_name"].confidence == "high"
    assert fields["landlord_name"].source_excerpt in text

    assert fields["tenant_name"].value == "Ahmed Al-Sayed"
    assert fields["unit_id"].value == "MC-B-1204"
    assert fields["start_date"].value == "2026-03-01"
    assert fields["end_date"].value == "2027-02-28"
    assert fields["term_months"].value == 12
    # Money is an exact decimal string, never a float -- see stub.py's _money().
    assert fields["rent_amount"].value == "8500"
    assert fields["rent_frequency"].value == "monthly"
    assert fields["annual_rent"].value == "102000"
    assert fields["deposit_amount"].value == "8500"
    assert fields["escalation_clause"].value["is_defined"] is True
    assert fields["landlord_signed"].value is True
    assert fields["tenant_signed"].value is True


def test_every_found_field_has_a_source_excerpt_that_is_a_real_substring():
    text = FIXTURE_LEASE.read_text()
    result = StubModelProvider().extract_lease(text)
    for field in result.fields:
        if field.confidence == "not_found":
            assert field.value is None
            assert field.source_excerpt is None
        else:
            assert field.source_excerpt is not None
            assert field.source_excerpt in text


def test_missing_fields_are_flagged():
    sparse_text = "This document does not look like a lease at all."
    result = StubModelProvider().extract_lease(sparse_text)
    flagged_fields = {f.field_name for f in result.flags}
    assert "landlord_name" in flagged_fields
    assert "tenant_name" in flagged_fields
    assert "unit_id" in flagged_fields


def test_end_before_start_is_flagged_as_a_contradiction():
    text = (
        "Landlord: Test Co\n\nTenant: Test Tenant\n\n"
        "This lease shall commence on 2027-01-01 and shall terminate on 2026-01-01, "
        "for a total term of 12 months."
    )
    result = StubModelProvider().extract_lease(text)
    reasons = [f.description for f in result.flags]
    assert any("not after" in r.lower() for r in reasons)


def test_analyze_photos_uses_filename_hints():
    class FakeImage:
        def __init__(self, filename):
            self.filename = filename
            self.path = filename

    images = [
        FakeImage("unit-1204-ac-worn.png"),
        FakeImage("unit-1204-water-heater-new.png"),
        FakeImage("unit-1204-wall-damage.png"),
    ]
    result = StubModelProvider().analyze_photos(images)

    assert "AC unit" in result.detected_contents
    assert "water heater" in result.detected_contents
    assert "wall/paint finish" in result.detected_contents
    assert any("worn" in d for d in result.damages)
    assert any("damaged" in d for d in result.damages)
    assert result.draft_work_order is not None
    assert result.draft_work_order.severity == "high"


def test_analyze_photos_no_damage_no_work_order():
    class FakeImage:
        def __init__(self, filename):
            self.filename = filename
            self.path = filename

    result = StubModelProvider().analyze_photos([FakeImage("unit-0301-fridge-new.png")])
    assert result.damages == []
    assert result.draft_work_order is None
