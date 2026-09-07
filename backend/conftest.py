"""Root conftest: sets dummy env vars so importing db.session / app config
doesn't blow up during test collection. Tests that need a real Postgres or
RabbitMQ connection set their own fixtures/markers — this only unblocks
import-time env var reads for tests that don't actually touch the network.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
