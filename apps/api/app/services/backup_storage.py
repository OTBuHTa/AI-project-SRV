from pathlib import Path
import hashlib
import os
import shutil


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


class LocalStorageAdapter:
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

    def delete(self, path: Path | str) -> bool:
        root = self.root.resolve()
        target = Path(path).resolve()

        try:
            target.relative_to(root)
        except ValueError as exc:
            raise RuntimeError(
                f"refusing to delete path outside backup root: {target}"
            ) from exc

        if not target.exists():
            return False

        if not target.is_file():
            raise RuntimeError(
                f"refusing to delete non-file backup artifact: {target}"
            )

        target.unlink()
        return True


class NasStorageAdapter(LocalStorageAdapter):
    """
    NAS backend through an OS-mounted filesystem.

    The application does not manage SMB/NFS credentials or mounts.
    The host/container is responsible for exposing the NAS mount.
    """

    def __init__(self, root: str):
        path = Path(root)

        if not path.exists():
            raise RuntimeError(
                f"NAS backup root does not exist: {root}"
            )

        if not path.is_dir():
            raise RuntimeError(
                f"NAS backup root is not a directory: {root}"
            )

        self.root = path


def get_backup_storage():
    backend = os.getenv(
        "BACKUP_STORAGE_BACKEND",
        "local",
    ).lower()

    if backend == "local":
        root = os.getenv(
            "BACKUP_STORAGE_ROOT",
            "/var/lib/ai-project-srv/backups",
        )
        return LocalStorageAdapter(root)

    if backend == "nas":
        root = os.getenv(
            "BACKUP_NAS_ROOT",
            "/mnt/ai-project-srv-backups",
        )
        return NasStorageAdapter(root)

    raise RuntimeError(
        f"unsupported backup storage backend: {backend}"
    )


def probe_backup_storage() -> dict:
    storage = get_backup_storage()

    root = storage.root
    root.mkdir(parents=True, exist_ok=True)

    probe = root / ".health-probe"

    try:
        probe.write_text("ok", encoding="utf-8")
        readable = probe.read_text(encoding="utf-8") == "ok"
        probe.unlink()

        return {
            "backend": storage.__class__.__name__,
            "root": str(root),
            "writable": True,
            "readable": readable,
            "healthy": readable,
        }

    except OSError as exc:
        return {
            "backend": storage.__class__.__name__,
            "root": str(root),
            "writable": False,
            "readable": False,
            "healthy": False,
            "error": "backup_storage_unavailable",
        }
