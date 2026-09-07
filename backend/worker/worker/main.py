"""Worker entrypoint. Run with: uv run python -m worker.main

Consumes both queues, dispatches to the matching handler, and manages the
Job status lifecycle + bounded retry / dead-letter per
docs/context/05-pipeline-architecture.md.
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime

import aio_pika

from db.models import Job, JobStatus
from db.session import async_session_factory
from worker.config import LEASE_EXTRACTION_QUEUE, MAX_RETRIES, PHOTO_ANALYSIS_QUEUE, RABBITMQ_URL
from worker.deps import get_provider, get_storage
from worker.handlers.lease_extraction import handle_lease_extraction
from worker.handlers.photo_analysis import handle_photo_analysis
from worker.queue import declare_topology

HANDLERS = {
    LEASE_EXTRACTION_QUEUE: handle_lease_extraction,
    PHOTO_ANALYSIS_QUEUE: handle_photo_analysis,
}


async def _handle_message(queue_name: str, message: aio_pika.abc.AbstractIncomingMessage) -> None:
    payload = json.loads(message.body)
    job_id = uuid.UUID(payload["job_id"])
    storage = get_storage()
    provider = get_provider()

    async with async_session_factory() as session:
        job = await session.get(Job, job_id)
        if job is None:
            # Unknown job id -- ack so a stale/malformed message doesn't loop forever.
            await message.ack()
            return

        job.status = JobStatus.PROCESSING
        await session.commit()

        try:
            await HANDLERS[queue_name](job_id, session, storage, provider)
        except Exception as exc:  # deliberately broad -- this is the job failure boundary
            await session.rollback()
            job = await session.get(Job, job_id)
            job.retry_count += 1
            if job.retry_count <= MAX_RETRIES:
                job.status = JobStatus.QUEUED
                await session.commit()
                await message.nack(requeue=True)
            else:
                job.status = JobStatus.FAILED
                job.error = str(exc)
                await session.commit()
                await message.nack(requeue=False)  # dead-lettered per worker/queue.py topology
            return

        job = await session.get(Job, job_id)
        job.status = JobStatus.DONE
        job.completed_at = datetime.now(UTC).replace(tzinfo=None)
        await session.commit()
        await message.ack()


async def _consume(queue: aio_pika.abc.AbstractQueue, queue_name: str) -> None:
    async with queue.iterator() as it:
        async for message in it:
            await _handle_message(queue_name, message)


async def main() -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=4)
        queues = await declare_topology(channel)
        print(f"Worker listening on: {', '.join(queues)}", flush=True)
        await asyncio.gather(*(_consume(queue, name) for name, queue in queues.items()))


if __name__ == "__main__":
    asyncio.run(main())
