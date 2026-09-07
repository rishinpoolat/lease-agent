from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase

from db.enums import Confidence, JobStatus, JobType, ReviewStatus, RuleVerdict, Severity, UnitStatus


def _pg_enum(enum_cls: type, name: str) -> SAEnum:
    """Every enum here is a (str, Enum) whose *value* is the wire/DB
    representation (lowercase snake_case, or PASS/FAIL/NOT_DETERMINABLE for
    RuleVerdict) -- values_callable is required because SQLAlchemy's default
    Enum type writes the Python member *name* (e.g. "AVAILABLE"), not
    `.value` ("available"), which would silently mismatch the enum labels
    Alembic actually created in Postgres."""
    return SAEnum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj])


class Base(DeclarativeBase):
    type_annotation_map = {
        UnitStatus: _pg_enum(UnitStatus, "unitstatus"),
        Confidence: _pg_enum(Confidence, "confidence"),
        ReviewStatus: _pg_enum(ReviewStatus, "reviewstatus"),
        Severity: _pg_enum(Severity, "severity"),
        RuleVerdict: _pg_enum(RuleVerdict, "ruleverdict"),
        JobType: _pg_enum(JobType, "jobtype"),
        JobStatus: _pg_enum(JobStatus, "jobstatus"),
    }
