"""Covers the redelivery-safety claim in
docs/context/05-pipeline-architecture.md: a lease.extraction message
delivered twice must not produce duplicate LeaseField/Flag/RuleEvaluation
rows. Needs a real Postgres -- see backend/conftest.py's `db_session`."""

from pathlib import Path

from agents.stub import StubModelProvider
from sqlalchemy import select
from storage.storage import LocalDiskStorage

from db.models import Flag, Job, JobType, Lease, LeaseField, RuleEvaluation
from worker.handlers.lease_extraction import handle_lease_extraction

SAMPLE_TEXT = (
    "Landlord: Acme Holdings\n\n"
    "Tenant: Jane Doe\n\n"
    "This lease shall commence on 2026-01-01 and shall terminate on 2027-01-01, "
    "for a total term of 12 months.\n\n"
    "The Tenant shall pay rent of QAR 5,000 per month.\n\n"
    "The Tenant shall pay a security deposit of QAR 5,000 upon signing.\n\n"
)


async def test_redelivery_does_not_duplicate_rows(db_session, tmp_path: Path):
    storage = LocalDiskStorage(tmp_path)
    ref = storage.save("lease.txt", SAMPLE_TEXT.encode())

    job = Job(type=JobType.LEASE_EXTRACTION)
    db_session.add(job)
    await db_session.flush()

    lease = Lease(source_file_ref=ref, extraction_job_id=job.id)
    db_session.add(lease)
    await db_session.commit()

    provider = StubModelProvider()

    # Simulate at-least-once redelivery: the same job processed twice.
    await handle_lease_extraction(job.id, db_session, storage, provider)
    await handle_lease_extraction(job.id, db_session, storage, provider)

    fields = (await db_session.scalars(select(LeaseField).where(LeaseField.lease_id == lease.id))).all()
    field_names = [f.field_name for f in fields]
    assert len(field_names) == len(set(field_names)), "redelivery duplicated LeaseField rows"
    assert len(field_names) > 0

    rule_evals = (
        await db_session.scalars(select(RuleEvaluation).where(RuleEvaluation.lease_id == lease.id))
    ).all()
    rule_ids = [r.rule_id for r in rule_evals]
    assert len(rule_ids) == len(set(rule_ids)), "redelivery duplicated RuleEvaluation rows"
    assert set(rule_ids) == {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}

    flags = (await db_session.scalars(select(Flag).where(Flag.lease_id == lease.id))).all()
    # No assertion on flag content here -- just that a third run wouldn't grow this list.
    flags_before_third_run = len(flags)
    await handle_lease_extraction(job.id, db_session, storage, provider)
    flags_after_third_run = (
        await db_session.scalars(select(Flag).where(Flag.lease_id == lease.id))
    ).all()
    assert len(flags_after_third_run) == flags_before_third_run
