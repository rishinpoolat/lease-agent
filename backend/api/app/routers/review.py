"""Human accept/reject/edit endpoints — see docs/context/06-human-in-the-loop-ux.md.

Reject is always non-destructive: it changes review_status only, never
deletes the underlying row or overwrites the agent's original value.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_session
from app.schemas import FlagOut, LeaseFieldOut, LeaseOut, ReviewAction, RuleEvaluationOut, WorkOrderOut
from app.ruleset import rule_severities, severity_sort_key
from db.models import Flag, Lease, LeaseField, ReviewStatus, RuleVerdict, Unit, UnitStatus, WorkOrder

router = APIRouter(tags=["review"])


def _apply_field_action(field: LeaseField, action: ReviewAction) -> None:
    if action.action == "accept":
        field.review_status = ReviewStatus.ACCEPTED
    elif action.action == "reject":
        field.review_status = ReviewStatus.REJECTED
    elif action.action == "edit":
        field.edited_value = action.edited_value
        field.review_status = ReviewStatus.EDITED


def _apply_simple_action(row: Flag | WorkOrder, action: ReviewAction) -> None:
    if action.action == "edit":
        raise HTTPException(status_code=400, detail="Only accept/reject are supported here")
    row.review_status = ReviewStatus.ACCEPTED if action.action == "accept" else ReviewStatus.REJECTED


@router.post("/lease-fields/{field_id}/review", response_model=LeaseFieldOut)
async def review_lease_field(field_id: uuid.UUID, action: ReviewAction, session: AsyncSession = Depends(get_session)):
    field = await session.get(LeaseField, field_id)
    if field is None:
        raise HTTPException(status_code=404, detail="Lease field not found")
    _apply_field_action(field, action)
    await session.commit()
    return LeaseFieldOut(
        id=field.id, field_name=field.field_name, value=field.value, confidence=field.confidence.value,
        source_excerpt=field.source_excerpt, review_status=field.review_status.value,
        edited_value=field.edited_value,
    )


@router.post("/flags/{flag_id}/review", response_model=FlagOut)
async def review_flag(flag_id: uuid.UUID, action: ReviewAction, session: AsyncSession = Depends(get_session)):
    flag = await session.get(Flag, flag_id)
    if flag is None:
        raise HTTPException(status_code=404, detail="Flag not found")
    _apply_simple_action(flag, action)
    await session.commit()
    return FlagOut(
        id=flag.id, field_name=flag.field_name, description=flag.description,
        severity=flag.severity.value, review_status=flag.review_status.value,
    )


@router.post("/work-orders/{work_order_id}/review", response_model=WorkOrderOut)
async def review_work_order(work_order_id: uuid.UUID, action: ReviewAction, session: AsyncSession = Depends(get_session)):
    work_order = await session.get(WorkOrder, work_order_id)
    if work_order is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    _apply_simple_action(work_order, action)
    await session.commit()
    return WorkOrderOut(
        id=work_order.id, title=work_order.title, description=work_order.description,
        severity=work_order.severity.value, review_status=work_order.review_status.value,
    )


@router.post("/leases/{lease_id}/accept-unit-match", response_model=LeaseOut)
async def accept_unit_match(lease_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """The one occupancy-mutating action in the system — see 'R7 and
    occupancy' in docs/context/03-validation-rules.md. Unit.status only
    flips to occupied here, after both R7 PASS and this explicit human
    acceptance; never on R7 PASS alone."""
    lease = await session.get(
        Lease, lease_id,
        options=[selectinload(Lease.fields), selectinload(Lease.flags), selectinload(Lease.rule_evaluations)],
    )
    if lease is None:
        raise HTTPException(status_code=404, detail="Lease not found")
    if lease.unit_id is None:
        raise HTTPException(status_code=400, detail="Lease has no matched unit to accept")

    lease.unit_match_accepted = True

    r7 = next((r for r in lease.rule_evaluations if r.rule_id == "R7"), None)
    if r7 is not None and r7.verdict == RuleVerdict.PASS:
        unit = await session.get(Unit, lease.unit_id)
        if unit is not None:
            unit.status = UnitStatus.OCCUPIED

    await session.commit()

    severities = rule_severities()
    rule_evaluations = sorted(
        (
            RuleEvaluationOut(
                id=r.id, rule_id=r.rule_id, verdict=r.verdict.value, reason=r.reason,
                severity=severities.get(r.rule_id, "low"), source_field_refs=r.source_field_refs,
            )
            for r in lease.rule_evaluations
        ),
        key=lambda r: severity_sort_key(r.severity),
    )
    return LeaseOut(
        id=lease.id, source_file_ref=lease.source_file_ref, uploaded_at=lease.uploaded_at,
        unit_match_accepted=lease.unit_match_accepted,
        fields=[
            LeaseFieldOut(
                id=f.id, field_name=f.field_name, value=f.value, confidence=f.confidence.value,
                source_excerpt=f.source_excerpt, review_status=f.review_status.value, edited_value=f.edited_value,
            )
            for f in lease.fields
        ],
        flags=[
            FlagOut(id=fl.id, field_name=fl.field_name, description=fl.description, severity=fl.severity.value, review_status=fl.review_status.value)
            for fl in lease.flags
        ],
        rule_evaluations=rule_evaluations,
    )
