"""Static unit label/id reference, read live from docs/units.json.

Used by stub.py to *identify* which unit a lease refers to (label -> unit_id
matching). Never used for `status` — occupancy is mutable at runtime, so
status must always come from the database, not this static file. See
docs/context/03-validation-rules.md.
"""

import json
from pathlib import Path

from pydantic import BaseModel

from agents.paths import resolve_path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_UNITS_PATH = resolve_path("UNITS_JSON_PATH", REPO_ROOT / "docs" / "units.json")


class UnitLabel(BaseModel):
    unit_id: str
    label: str
    building_name: str
    property_name: str


def load_unit_labels(path: Path = DEFAULT_UNITS_PATH) -> list[UnitLabel]:
    data = json.loads(path.read_text())
    labels: list[UnitLabel] = []
    for prop in data["properties"]:
        for building in prop["buildings"]:
            for unit in building["units"]:
                labels.append(
                    UnitLabel(
                        unit_id=unit["unit_id"],
                        label=unit["label"],
                        building_name=building["name"],
                        property_name=prop["name"],
                    )
                )
    return labels
