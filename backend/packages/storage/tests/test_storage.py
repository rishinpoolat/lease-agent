from pathlib import Path

import pytest
from storage.storage import LocalDiskStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalDiskStorage:
    return LocalDiskStorage(tmp_path / "uploads")


def test_save_and_read_round_trip(storage: LocalDiskStorage):
    ref = storage.save("lease.txt", b"hello world")
    assert storage.read_bytes(ref) == b"hello world"
    assert storage.read_text(ref) == "hello world"


def test_save_strips_directory_traversal_from_filename(storage: LocalDiskStorage):
    ref = storage.save("../../../../etc/cron.d/evil", b"payload")
    # The ref must not escape the storage root -- the malicious path
    # components are stripped, only the basename survives.
    assert ".." not in ref
    assert "/" not in ref
    assert ref.endswith("_evil")
    saved_path = (storage.root / ref).resolve()
    assert storage.root.resolve() in saved_path.parents


def test_save_strips_absolute_path_from_filename(storage: LocalDiskStorage):
    ref = storage.save("/etc/passwd", b"payload")
    assert ref.endswith("_passwd")
    saved_path = (storage.root / ref).resolve()
    assert storage.root.resolve() in saved_path.parents


def test_read_rejects_a_ref_that_resolves_outside_root(storage: LocalDiskStorage):
    with pytest.raises(ValueError):
        storage.read_bytes("../../../../etc/passwd")
