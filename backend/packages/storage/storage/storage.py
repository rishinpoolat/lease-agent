"""Storage boundary — see ADR-008 in docs/context/07-decisions.md.

`save`/`read_bytes`/`read_text` deal in storage *refs* (opaque relative
keys), never filesystem paths directly — that's what makes swapping
LocalDiskStorage for a GCS/S3-backed implementation later a constructor
change, not a call-site change. Shared by apps/api (writes on upload) and
apps/worker (reads during processing) so both sides speak the same
interface.
"""

import uuid
from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    def save(self, filename: str, content: bytes) -> str:
        """Persists `content`, returns a ref to pass back to read_* later."""
        ...

    def read_bytes(self, ref: str) -> bytes: ...

    def read_text(self, ref: str) -> str: ...


class LocalDiskStorage:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> str:
        ref = f"{uuid.uuid4()}_{filename}"
        (self.root / ref).write_bytes(content)
        return ref

    def read_bytes(self, ref: str) -> bytes:
        return (self.root / ref).read_bytes()

    def read_text(self, ref: str) -> str:
        return (self.root / ref).read_text()
