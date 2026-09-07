"""Root conftest: sets dummy env vars so importing db.session / app config
doesn't blow up during test collection, and provides `db_session` for tests
that need a real Postgres (worker idempotency, occupancy-write gating).

Those tests skip automatically if TEST_DATABASE_URL isn't set or isn't
reachable -- CI provides a real Postgres service container (see
.github/workflows/ci.yml); locally, point TEST_DATABASE_URL at a disposable
Postgres (e.g. the one docker-compose already runs) to run them.
"""

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def db_session():
    from db.base import Base  # local import: only needed once DATABASE_URL is real

    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set -- skipping Postgres integration test")

    engine = create_async_engine(TEST_DATABASE_URL)
    try:
        async with engine.connect():
            pass
    except Exception as exc:  # noqa: BLE001 -- any connection failure means "skip", not "fail"
        await engine.dispose()
        pytest.skip(f"Postgres at TEST_DATABASE_URL not reachable: {exc}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
