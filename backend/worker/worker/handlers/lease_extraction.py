"""Handles a lease.extraction job — see docs/context/05-pipeline-architecture.md
and docs/context/03-validation-rules.md.

Idempotent by design: on redelivery, this deletes and reinserts the lease's
LeaseField/Flag/RuleEvaluation rows inside one transaction rather than
upserting per-row, so a duplicate delivery produces the same end state, not
duplicate rows.
"""

import uuid

from agents.provider import ModelProvider
from agents.rules import UnitRecord, evaluate_rules
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from storage.storage import Storage

from db.models import Confidence, Flag, Lease, LeaseField, RuleEvaluation, RuleVerdict, Severity, Unit
from worker.document_text import read_document_text


async def _load_unit_records(session: AsyncSession) -> dict[str, UnitRecord]:
    units = (await session.scalars(select(Unit))).all()
    return {u.unit_id: UnitRecord(unit_id=u.unit_id, label=u.label, status=u.status.value) for u in units}


async def handle_lease_extraction(job_id: uuid.UUID, session: AsyncSession, storage: Storage, provider: ModelProvider) -> None:
    lease = (await session.scalars(select(Lease).where(Lease.extraction_job_id == job_id))).one()

    document_text = read_document_text(storage, lease.source_file_ref)
    result = provider.extract_lease(document_text)

    await session.execute(delete(LeaseField).where(LeaseField.lease_id == lease.id))
    await session.execute(delete(Flag).where(Flag.lease_id == lease.id))
    await session.execute(delete(RuleEvaluation).where(RuleEvaluation.lease_id == lease.id))
    await session.flush()

    for f in result.fields:
        session.add(
            LeaseField(
                lease_id=lease.id, field_name=f.field_name, value=f.value,
                confidence=Confidence(f.confidence), source_excerpt=f.source_excerpt,
            )
        )
    for fl in result.flags:
        session.add(
            Flag(
                lease_id=lease.id, field_name=fl.field_name, description=fl.description,
                severity=Severity(fl.severity),
            )
        )

    units = await _load_unit_records(session)
    unit_field = next(
        (f for f in result.fields if f.field_name == "unit_id" and f.confidence != "not_found"), None
    )
    if unit_field is not None and str(unit_field.value) in units:
        lease.unit_id = str(unit_field.value)

    for r in evaluate_rules(result.fields, units):
        session.add(
            RuleEvaluation(
                lease_id=lease.id, rule_id=r.rule_id, verdict=RuleVerdict(r.verdict),
                reason=r.reason, source_field_refs=r.source_field_refs,
            )
        )

    await session.commit()
