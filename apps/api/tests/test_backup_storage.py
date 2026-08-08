from pathlib import Path

from app.services.backup_storage import (
    LocalStorageAdapter,
    sha256_file,
)


def test_local_storage_copy_and_verify(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("AI-project SRV", encoding="utf-8")

    storage = LocalStorageAdapter(
        str(tmp_path / "storage")
    )

    digest = sha256_file(source)

    stored = storage.put(
        source,
        "workspace/test/source.txt",
    )

    assert stored.exists()
    assert storage.verify(stored, digest)
