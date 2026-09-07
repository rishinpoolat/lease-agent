import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Value = str | int | float | bool | dict | list | None


class UnitSummary(BaseModel):
    unit_id: str
    label: str
    building_name: str
    property_name: str
    type: str
    status: str


class LeaseFieldOut(BaseModel):
    id: uuid.UUID
    field_name: str
    value: Value
    confidence: str
    source_excerpt: str | None
    review_status: str
    edited_value: Value


class FlagOut(BaseModel):
    id: uuid.UUID
    field_name: str | None
    description: str
    severity: str
    review_status: str


class RuleEvaluationOut(BaseModel):
    id: uuid.UUID
    rule_id: str
    verdict: str
    reason: str
    severity: str
    source_field_refs: list[str]


class LeaseOut(BaseModel):
    id: uuid.UUID
    source_file_ref: str
    uploaded_at: datetime
    unit_match_accepted: bool
    fields: list[LeaseFieldOut]
    flags: list[FlagOut]
    rule_evaluations: list[RuleEvaluationOut]


class WorkOrderOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    severity: str
    review_status: str


class PhotoReportOut(BaseModel):
    id: uuid.UUID
    uploaded_at: datetime
    photo_refs: list[str]
    condition_assessment: str | None
    detected_contents: list[str]
    damages: list[str]
    work_orders: list[WorkOrderOut]


class UnitDetail(UnitSummary):
    lease: LeaseOut | None
    photo_reports: list[PhotoReportOut]


class JobOut(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    error: str | None


class UploadAccepted(BaseModel):
    job_id: uuid.UUID


class ReviewAction(BaseModel):
    action: Literal["accept", "reject", "edit"]
    edited_value: Value = None
