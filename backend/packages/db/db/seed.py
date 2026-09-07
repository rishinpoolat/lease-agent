"""Loads docs/units.json into the units table. Run with:

    uv run python -m db.seed

Idempotent — re-running upserts by unit_id rather than duplicating rows, so
it's safe to run every time the stack starts up.
"""

import asyncio
import json
import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Unit, UnitStatus
from db.session import async_session_factory

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_UNITS_PATH = REPO_ROOT / "docs" / "units.json"


def _load_units(units_json_path: Path) -> list[dict]:
    data = json.loads(units_json_path.read_text())
    units: list[dict] = []
    for prop in data["properties"]:
        for building in prop["buildings"]:
            for unit in building["units"]:
                units.append(
                    {
                        "unit_id": unit["unit_id"],
                        "property_id": prop["property_id"],
                        "property_name": prop["name"],
                        "building_id": building["building_id"],
                        "building_name": building["name"],
                        "label": unit["label"],
                        "type": unit["type"],
                        "area_sqm": unit["area_sqm"],
                        "parking_bay": unit["parking_bay"],
                        "status": UnitStatus(unit["status"]),
                    }
                )
    return units


async def seed(session: AsyncSession, units_json_path: Path = DEFAULT_UNITS_PATH) -> int:
    units = _load_units(units_json_path)
    count = 0
    for unit_data in units:
        existing = await session.scalar(
            select(Unit).where(Unit.unit_id == unit_data["unit_id"])
        )
        if existing:
            # `status` is excluded deliberately: it's mutable at runtime
            # (occupancy flips via the review flow, not this seed file) --
            # re-syncing it here on every restart would silently revert a
            # real occupancy change back to units.json's static baseline,
            # which is exactly the kind of bug this comment exists to
            # prevent someone from reintroducing.
            for key, value in unit_data.items():
                if key != "status":
                    setattr(existing, key, value)
        else:
            session.add(Unit(**unit_data))
        count += 1
    await session.commit()
    return count


async def main() -> None:
    units_json_path = Path(os.environ.get("UNITS_JSON_PATH", DEFAULT_UNITS_PATH))
    async with async_session_factory() as session:
        count = await seed(session, units_json_path)
    print(f"Seeded {count} units from {units_json_path}")


if __name__ == "__main__":
    asyncio.run(main())
