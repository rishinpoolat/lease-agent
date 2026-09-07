"""RabbitMQ publishing. Topology matches docs/context/05-pipeline-architecture.md
exactly — two work queues, each dead-lettering to its own `*.dlq` queue via
the default exchange. apps/worker declares the identical topology on its
side (queue declaration is idempotent/identical either way)."""

import json

import aio_pika

from app.config import LEASE_EXTRACTION_QUEUE, PHOTO_ANALYSIS_QUEUE

QUEUES = (LEASE_EXTRACTION_QUEUE, PHOTO_ANALYSIS_QUEUE)


async def declare_topology(channel: aio_pika.abc.AbstractChannel) -> None:
    for queue_name in QUEUES:
        dlq_name = f"{queue_name}.dlq"
        await channel.declare_queue(dlq_name, durable=True)
        await channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": dlq_name,
            },
        )


async def publish_job(channel: aio_pika.abc.AbstractChannel, queue_name: str, job_id: str) -> None:
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps({"job_id": job_id}).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=queue_name,
    )
