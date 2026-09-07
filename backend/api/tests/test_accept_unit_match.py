"""Covers the one occupancy-mutating action in the system -- see 'R7 and
occupancy' in docs/context/03-validation-rules.md: Unit.status must only
flip to occupied when BOTH R7 has PASSed AND a human has explicitly
accepted the match, never on either alone. Needs a real Postgres -- see
backend/conftest.py's `db_session`."""

from app.routers.review import accept_unit_match
from db.models import Lease, RuleEvaluation, RuleVerdict, Unit, UnitStatus


def _make_unit(unit_id: str) -> Unit:
    return Unit(
        unit_id=unit_id, property_id="P", property_name="Test Property",
        building_id="B", building_name="Test Building", label=f"Unit {unit_id}",
        type="1BR", area_sqm=50, parking_bay="B-1", status=UnitStatus.AVAILABLE,
    )


async def test_occupancy_flips_when_r7_passed_and_match_accepted(db_session):
    unit = _make_unit("TEST-R7-PASS")
    db_session.add(unit)
    lease = Lease(source_file_ref="ref.txt", unit_id="TEST-R7-PASS")
    db_session.add(lease)
    await db_session.flush()
    db_session.add(
        RuleEvaluation(lease_id=lease.id, rule_id="R7", verdict=RuleVerdict.PASS, reason="ok", source_field_refs=["unit_id"])
    )
    await db_session.commit()

    assert (await db_session.get(Unit, "TEST-R7-PASS")).status == UnitStatus.AVAILABLE

    await accept_unit_match(lease.id, db_session)

    assert (await db_session.get(Unit, "TEST-R7-PASS")).status == UnitStatus.OCCUPIED
    assert (await db_session.get(Lease, lease.id)).unit_match_accepted is True


async def test_occupancy_does_not_flip_when_r7_failed_even_if_accepted(db_session):
    unit = _make_unit("TEST-R7-FAIL")
    db_session.add(unit)
    lease = Lease(source_file_ref="ref.txt", unit_id="TEST-R7-FAIL")
    db_session.add(lease)
    await db_session.flush()
    db_session.add(
        RuleEvaluation(lease_id=lease.id, rule_id="R7", verdict=RuleVerdict.FAIL, reason="already occupied", source_field_refs=["unit_id"])
    )
    await db_session.commit()

    await accept_unit_match(lease.id, db_session)

    # Acceptance is still recorded (a human did accept the match) -- it's
    # only the occupancy WRITE that's gated on R7, per design.
    assert (await db_session.get(Lease, lease.id)).unit_match_accepted is True
    assert (await db_session.get(Unit, "TEST-R7-FAIL")).status == UnitStatus.AVAILABLE


async def test_occupancy_does_not_flip_without_acceptance_call(db_session):
    """Sanity check on the gate's other half: no code path besides
    accept_unit_match should ever touch Unit.status. This just confirms the
    baseline -- inserting an R7 PASS row alone, with no acceptance call,
    leaves the unit untouched."""
    unit = _make_unit("TEST-NO-ACCEPT")
    db_session.add(unit)
    lease = Lease(source_file_ref="ref.txt", unit_id="TEST-NO-ACCEPT")
    db_session.add(lease)
    await db_session.flush()
    db_session.add(
        RuleEvaluation(lease_id=lease.id, rule_id="R7", verdict=RuleVerdict.PASS, reason="ok", source_field_refs=["unit_id"])
    )
    await db_session.commit()

    assert (await db_session.get(Unit, "TEST-NO-ACCEPT")).status == UnitStatus.AVAILABLE
