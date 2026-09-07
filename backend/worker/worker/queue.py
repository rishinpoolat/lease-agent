"""Identical topology to backend/api/app/queue.py — see
docs/context/05-pipeline-architecture.md for the shared source of truth.
Declaring the same durable queues/arguments from both sides is idempotent."""

import aio_pika

from worker.config import LEASE_EXTRACTION_QUEUE, PHOTO_ANALYSIS_QUEUE

QUEUES = (LEASE_EXTRACTION_QUEUE, PHOTO_ANALYSIS_QUEUE)


async def declare_topology(channel: aio_pika.abc.AbstractChannel) -> dict[str, aio_pika.abc.AbstractQueue]:
    queues = {}
    for queue_name in QUEUES:
        dlq_name = f"{queue_name}.dlq"
        await channel.declare_queue(dlq_name, durable=True)
        queues[queue_name] = await channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": dlq_name,
            },
        )
    return queues
