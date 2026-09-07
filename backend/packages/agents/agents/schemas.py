"""Transport shapes between a ModelProvider and the worker.

These mirror the LeaseField/Flag/PhotoReport/WorkOrder DB shapes in
packages/db/db/models.py but are plain Pydantic models, not ORM objects —
a ModelProvider must never depend on the DB layer (see
docs/context/04-agent-boundaries.md).
"""

from typing import Literal

from pydantic import BaseModel

Confidence = Literal["high", "low", "not_found"]
Severity = Literal["high", "medium", "low"]


class ExtractedField(BaseModel):
    field_name: str
    value: str | int | float | bool | dict | list | None
    confidence: Confidence
    # Verbatim substring of the input document, or None when confidence is
    # "not_found" — see the traceability contract in docs/context/02-domain-model.md.
    source_excerpt: str | None = None


class FlagCandidate(BaseModel):
    field_name: str | None
    description: str
    severity: Severity


class LeaseExtractionResult(BaseModel):
    fields: list[ExtractedField]
    flags: list[FlagCandidate]


class WorkOrderDraft(BaseModel):
    title: str
    description: str
    severity: Severity


class PhotoAssessmentResult(BaseModel):
    condition_assessment: str
    detected_contents: list[str]
    damages: list[str]
    # None when nothing in the photos warrants a work order (e.g. everything
    # assessed as new/undamaged) — a report shouldn't manufacture an issue.
    draft_work_order: WorkOrderDraft | None
