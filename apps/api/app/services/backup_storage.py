from pathlib import Path
import hashlib
import shutil


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


class LocalStorageAdapter:
    """
    Local implementation of the backup storage contract.

    The NAS adapter will implement the same interface so the BackupService
    does not depend directly on NFS/SMB/S3 details.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, source: Path, relative_path: str) -> Path:
        destination = self.root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, destination)

        return destination

    def verify(self, path: Path, expected_sha256: str) -> bool:
        return sha256_file(path) == expected_sha256
