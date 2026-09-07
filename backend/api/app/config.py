import os
from pathlib import Path

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
LEASE_EXTRACTION_QUEUE = "lease.extraction"
PHOTO_ANALYSIS_QUEUE = "photo.analysis"

STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "./data/uploads")).resolve()
