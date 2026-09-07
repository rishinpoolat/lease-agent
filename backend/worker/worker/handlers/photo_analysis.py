"""Handles a photo.analysis job — see docs/context/05-pipeline-architecture.md.

Idempotent the same way as lease_extraction: existing work orders for this
photo report are deleted and reinserted inside one transaction on
redelivery.
"""

import uuid
from dataclasses import dataclass

from agents.provider import ModelProvider
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from storage.storage import Storage

from db.models import PhotoReport, Severity, WorkOrder


@dataclass
class StoredImage:
    """Satisfies agents.provider.ImageRef. `filename` is the storage ref
    (uuid_originalname) — still contains the original filename as a suffix,
    which is what the stub's filename-hint heuristics key off."""

    filename: str
    path: str


async def handle_photo_analysis(job_id: uuid.UUID, session: AsyncSession, storage: Storage, provider: ModelProvider) -> None:
    photo_report = (
        await session.scalars(
            select(PhotoReport)
            .where(PhotoReport.analysis_job_id == job_id)
            .options(selectinload(PhotoReport.work_orders))
        )
    ).one()

    images = [StoredImage(filename=ref, path=ref) for ref in photo_report.photo_refs]
    result = provider.analyze_photos(images)

    photo_report.condition_assessment = result.condition_assessment
    photo_report.detected_contents = result.detected_contents
    photo_report.damages = result.damages

    await session.execute(delete(WorkOrder).where(WorkOrder.photo_report_id == photo_report.id))
    await session.flush()

    if result.draft_work_order is not None:
        session.add(
            WorkOrder(
                photo_report_id=photo_report.id,
                unit_id=photo_report.unit_id,
                title=result.draft_work_order.title,
                description=result.draft_work_order.description,
                severity=Severity(result.draft_work_order.severity),
            )
        )

    await session.commit()
