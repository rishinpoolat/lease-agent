"""SQLAlchemy models.

Shapes follow docs/context/02-domain-model.md exactly — see that file for
the *why* behind each choice, especially the traceability contract
(value/confidence/source_excerpt/review_status on every extracted field) and
ADR-006 (LeaseField as rows, not fixed columns) in
docs/context/07-decisions.md.

Idempotency note (docs/context/05-pipeline-architecture.md): LeaseField,
Flag, and RuleEvaluation rows are owned by `lease_id`, and PhotoReport /
WorkOrder rows are owned by `analysis_job_id` / `photo_report_id`. Workers
achieve idempotent redelivery by deleting-then-reinserting a lease's (or
photo report's) child rows inside one transaction, not by upserting on a
per-row key — simpler, and correct because a worker handler is the only
writer of these rows.
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.enums import Confidence, JobStatus, JobType, ReviewStatus, RuleVerdict, Severity, UnitStatus

__all__ = [
    "Base",
    "Confidence",
    "Flag",
    "Job",
    "JobStatus",
    "JobType",
    "Lease",
    "LeaseField",
    "PhotoReport",
    "ReviewStatus",
    "RuleEvaluation",
    "RuleVerdict",
    "Severity",
    "Unit",
    "UnitStatus",
    "WorkOrder",
]


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[JobType] = mapped_column(nullable=False)
    status: Mapped[JobStatus] = mapped_column(nullable=False, default=JobStatus.QUEUED)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class Unit(Base):
    """Mirrors docs/units.json — seeded via db/seed.py, not created by the app."""

    __tablename__ = "units"

    unit_id: Mapped[str] = mapped_column(String, primary_key=True)
    property_id: Mapped[str] = mapped_column(String, nullable=False)
    property_name: Mapped[str] = mapped_column(String, nullable=False)
    building_id: Mapped[str] = mapped_column(String, nullable=False)
    building_name: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    area_sqm: Mapped[float] = mapped_column(nullable=False)
    parking_bay: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[UnitStatus] = mapped_column(nullable=False)

    leases: Mapped[list["Lease"]] = relationship(back_populates="unit")
    photo_reports: Mapped[list["PhotoReport"]] = relationship(back_populates="unit")
    work_orders: Mapped[list["WorkOrder"]] = relationship(back_populates="unit")


class Lease(Base):
    __tablename__ = "leases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_file_ref: Mapped[str] = mapped_column(String, nullable=False)
    unit_id: Mapped[str | None] = mapped_column(ForeignKey("units.unit_id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    extraction_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True, unique=True
    )
    # Set once a human accepts the unit match (see docs/context/03-validation-rules.md,
    # "R7 and occupancy") — occupancy is never flipped on R7 PASS alone.
    unit_match_accepted: Mapped[bool] = mapped_column(nullable=False, default=False)

    unit: Mapped[Unit | None] = relationship(back_populates="leases")
    fields: Mapped[list["LeaseField"]] = relationship(
        back_populates="lease", cascade="all, delete-orphan"
    )
    flags: Mapped[list["Flag"]] = relationship(
        back_populates="lease", cascade="all, delete-orphan"
    )
    rule_evaluations: Mapped[list["RuleEvaluation"]] = relationship(
        back_populates="lease", cascade="all, delete-orphan"
    )


class LeaseField(Base):
    """One row per extracted field per lease — see ADR-006."""

    __tablename__ = "lease_fields"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leases.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[dict | list | str | float | bool | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[Confidence] = mapped_column(nullable=False)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[ReviewStatus] = mapped_column(
        nullable=False, default=ReviewStatus.PENDING
    )
    # Never overwrites `value` — see docs/context/02-domain-model.md traceability contract.
    edited_value: Mapped[dict | list | str | float | bool | None] = mapped_column(
        JSONB, nullable=True
    )

    lease: Mapped[Lease] = relationship(back_populates="fields")


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leases.id"), nullable=False
    )
    field_name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(nullable=False)
    review_status: Mapped[ReviewStatus] = mapped_column(
        nullable=False, default=ReviewStatus.PENDING
    )

    lease: Mapped[Lease] = relationship(back_populates="flags")


class RuleEvaluation(Base):
    """Verdict per docs/owner_ruleset.json rule. Never store the rule's own
    description/check text here — read it live from the ruleset file."""

    __tablename__ = "rule_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leases.id"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String, nullable=False)  # "R1".."R7"
    verdict: Mapped[RuleVerdict] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_field_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    lease: Mapped[Lease] = relationship(back_populates="rule_evaluations")


class PhotoReport(Base):
    __tablename__ = "photo_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    unit_id: Mapped[str] = mapped_column(ForeignKey("units.unit_id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    photo_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    condition_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_contents: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    damages: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    analysis_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True, unique=True
    )

    unit: Mapped[Unit] = relationship(back_populates="photo_reports")
    work_orders: Mapped[list["WorkOrder"]] = relationship(
        back_populates="photo_report", cascade="all, delete-orphan"
    )


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    photo_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("photo_reports.id"), nullable=False
    )
    unit_id: Mapped[str] = mapped_column(ForeignKey("units.unit_id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(nullable=False)
    review_status: Mapped[ReviewStatus] = mapped_column(
        nullable=False, default=ReviewStatus.PENDING
    )

    photo_report: Mapped[PhotoReport] = relationship(back_populates="work_orders")
    unit: Mapped[Unit] = relationship(back_populates="work_orders")
