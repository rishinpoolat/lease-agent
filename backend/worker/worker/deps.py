from agents.provider import ModelProvider
from agents.stub import StubModelProvider
from storage.storage import LocalDiskStorage, Storage

from worker.config import STORAGE_DIR


def get_storage() -> Storage:
    return LocalDiskStorage(STORAGE_DIR)


def get_provider() -> ModelProvider:
    # The only place a ModelProvider is constructed — see
    # docs/context/04-agent-boundaries.md. Swapping in a real provider is a
    # one-line change here, nowhere else.
    return StubModelProvider()
