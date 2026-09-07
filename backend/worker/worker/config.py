import os
from pathlib import Path

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
LEASE_EXTRACTION_QUEUE = "lease.extraction"
PHOTO_ANALYSIS_QUEUE = "photo.analysis"

STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "./data/uploads")).resolve()

# Bounded retry per docs/context/05-pipeline-architecture.md — after this
# many failed attempts a job is marked failed and its message is
# dead-lettered (not silently dropped) rather than requeued forever.
MAX_RETRIES = int(os.environ.get("WORKER_MAX_RETRIES", "3"))
