from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import RABBITMQ_URL
from app.queue import declare_topology
from app.routers import jobs, leases, photos, review, units


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await declare_topology(channel)
    app.state.rabbitmq_connection = connection
    app.state.rabbitmq_channel = channel
    yield
    await channel.close()
    await connection.close()


app = FastAPI(title="Lease Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(units.router)
app.include_router(leases.router)
app.include_router(photos.router)
app.include_router(jobs.router)
app.include_router(review.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
