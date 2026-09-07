import aio_pika
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from storage.storage import Storage

from app.config import PHOTO_ANALYSIS_QUEUE
from app.deps import get_channel, get_session, get_storage
from app.queue import publish_job
from app.schemas import UploadAccepted
from db.models import Job, JobType, PhotoReport, Unit

router = APIRouter(tags=["photos"])


@router.post("/units/{unit_id}/photos", response_model=UploadAccepted, status_code=202)
async def upload_photos(
    unit_id: str,
    files: list[UploadFile],
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
    channel: aio_pika.abc.AbstractChannel = Depends(get_channel),
):
    unit = await session.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found")
    if not files:
        raise HTTPException(status_code=400, detail="At least one photo is required")

    refs = []
    for f in files:
        content = await f.read()
        refs.append(storage.save(f.filename, content))

    job = Job(type=JobType.PHOTO_ANALYSIS)
    session.add(job)
    await session.flush()

    photo_report = PhotoReport(unit_id=unit_id, photo_refs=refs, analysis_job_id=job.id)
    session.add(photo_report)
    await session.commit()

    await publish_job(channel, PHOTO_ANALYSIS_QUEUE, str(job.id))

    return UploadAccepted(job_id=job.id)
