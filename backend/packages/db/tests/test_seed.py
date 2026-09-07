from sqlalchemy import select

from db.models import Unit, UnitStatus
from db.seed import DEFAULT_UNITS_PATH, _load_units, seed


def test_loads_all_units_from_units_json():
    units = _load_units(DEFAULT_UNITS_PATH)
    unit_ids = {u["unit_id"] for u in units}
    assert "MC-B-1204" in unit_ids
    assert "MC-B-1205" in unit_ids
    assert len(units) == 5


def test_status_is_parsed_as_enum():
    units = _load_units(DEFAULT_UNITS_PATH)
    occupied = next(u for u in units if u["unit_id"] == "MC-B-1205")
    assert occupied["status"] == UnitStatus.OCCUPIED
    available = next(u for u in units if u["unit_id"] == "MC-B-1204")
    assert available["status"] == UnitStatus.AVAILABLE


async def test_reseeding_does_not_revert_a_live_occupancy_change(db_session):
    """Regression test: re-running seed() (which happens on every
    `docker compose up`, via the migrate service) must not silently revert
    an occupancy change made through the review flow back to units.json's
    static baseline -- this was a real bug caught during manual end-to-end
    testing, not a hypothetical."""
    await seed(db_session, DEFAULT_UNITS_PATH)

    unit = await db_session.get(Unit, "MC-B-1204")
    assert unit.status == UnitStatus.AVAILABLE  # units.json's baseline
    unit.status = UnitStatus.OCCUPIED
    await db_session.commit()

    await seed(db_session, DEFAULT_UNITS_PATH)

    refreshed = (await db_session.scalars(select(Unit).where(Unit.unit_id == "MC-B-1204"))).one()
    assert refreshed.status == UnitStatus.OCCUPIED, "re-seeding reverted a live occupancy change"

    # Non-status fields still stay in sync with units.json on reseed.
    assert refreshed.label == "Apartment 1204"
