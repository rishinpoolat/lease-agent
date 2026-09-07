from db.seed import DEFAULT_UNITS_PATH, _load_units
from db.models import UnitStatus


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
