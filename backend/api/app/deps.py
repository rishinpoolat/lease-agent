from collections.abc import AsyncGenerator

import aio_pika
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from storage.storage import LocalDiskStorage, Storage

from app.config import STORAGE_DIR
from db.session import get_session as _get_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_session():
        yield session


def get_storage() -> Storage:
    return LocalDiskStorage(STORAGE_DIR)


def get_channel(request: Request) -> aio_pika.abc.AbstractChannel:
    return request.app.state.rabbitmq_channel
