from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_session
from app.ruleset import rule_severities, severity_sort_key
from app.schemas import (
    FlagOut,
    LeaseFieldOut,
    LeaseOut,
    PhotoReportOut,
    RuleEvaluationOut,
    UnitDetail,
    UnitSummary,
    WorkOrderOut,
)
from db.models import Lease, PhotoReport, Unit

router = APIRouter(tags=["units"])


@router.get("/units", response_model=list[UnitSummary])
async def list_units(session: AsyncSession = Depends(get_session)):
    units = (await session.scalars(select(Unit).order_by(Unit.unit_id))).all()
    return [
        UnitSummary(
            unit_id=u.unit_id, label=u.label, building_name=u.building_name,
            property_name=u.property_name, type=u.type, status=u.status.value,
        )
        for u in units
    ]


@router.get("/units/{unit_id}", response_model=UnitDetail)
async def get_unit(unit_id: str, session: AsyncSession = Depends(get_session)):
    unit = await session.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found")

    lease = (
        await session.scalars(
            select(Lease)
            .where(Lease.unit_id == unit_id)
            .options(
                selectinload(Lease.fields),
                selectinload(Lease.flags),
                selectinload(Lease.rule_evaluations),
            )
            .order_by(Lease.uploaded_at.desc())
        )
    ).first()

    photo_reports = (
        await session.scalars(
            select(PhotoReport)
            .where(PhotoReport.unit_id == unit_id)
            .options(selectinload(PhotoReport.work_orders))
            .order_by(PhotoReport.uploaded_at.desc())
        )
    ).all()

    lease_out = None
    if lease is not None:
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
        lease_out = LeaseOut(
            id=lease.id,
            source_file_ref=lease.source_file_ref,
            uploaded_at=lease.uploaded_at,
            unit_match_accepted=lease.unit_match_accepted,
            fields=[
                LeaseFieldOut(
                    id=f.id, field_name=f.field_name, value=f.value, confidence=f.confidence.value,
                    source_excerpt=f.source_excerpt, review_status=f.review_status.value,
                    edited_value=f.edited_value,
                )
                for f in lease.fields
            ],
            flags=[
                FlagOut(
                    id=fl.id, field_name=fl.field_name, description=fl.description,
                    severity=fl.severity.value, review_status=fl.review_status.value,
                )
                for fl in lease.flags
            ],
            rule_evaluations=rule_evaluations,
        )

    return UnitDetail(
        unit_id=unit.unit_id, label=unit.label, building_name=unit.building_name,
        property_name=unit.property_name, type=unit.type, status=unit.status.value,
        lease=lease_out,
        photo_reports=[
            PhotoReportOut(
                id=pr.id, uploaded_at=pr.uploaded_at, photo_refs=pr.photo_refs,
                condition_assessment=pr.condition_assessment, detected_contents=pr.detected_contents,
                damages=pr.damages,
                work_orders=[
                    WorkOrderOut(
                        id=wo.id, title=wo.title, description=wo.description,
                        severity=wo.severity.value, review_status=wo.review_status.value,
                    )
                    for wo in pr.work_orders
                ],
            )
            for pr in photo_reports
        ],
    )
