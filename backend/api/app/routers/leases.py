import aio_pika
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from storage.storage import Storage

from app.config import LEASE_EXTRACTION_QUEUE
from app.deps import get_channel, get_session, get_storage
from app.queue import publish_job
from app.schemas import UploadAccepted
from db.models import Job, JobType, Lease

router = APIRouter(tags=["leases"])


@router.post("/leases", response_model=UploadAccepted, status_code=202)
async def upload_lease(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    storage: Storage = Depends(get_storage),
    channel: aio_pika.abc.AbstractChannel = Depends(get_channel),
):
    content = await file.read()
    ref = storage.save(file.filename, content)

    job = Job(type=JobType.LEASE_EXTRACTION)
    session.add(job)
    await session.flush()

    lease = Lease(source_file_ref=ref, extraction_job_id=job.id)
    session.add(lease)
    await session.commit()

    # Known simplification: publish-after-commit, not a transactional
    # outbox. If the publish fails here the job stays queued forever with
    # no message in flight — acceptable for this build's scope, called out
    # in the README as the real fix for production (outbox table + relay).
    await publish_job(channel, LEASE_EXTRACTION_QUEUE, str(job.id))

    return UploadAccepted(job_id=job.id)
