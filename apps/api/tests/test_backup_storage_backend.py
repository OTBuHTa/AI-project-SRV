from pathlib import Path

import pytest

from app.services.backup_storage import (
    LocalStorageAdapter,
    NasStorageAdapter,
    get_backup_storage,
)


def test_local_storage_backend(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("BACKUP_STORAGE_BACKEND", "local")
    monkeypatch.setenv("BACKUP_STORAGE_ROOT", str(tmp_path))

    storage = get_backup_storage()

    assert isinstance(storage, LocalStorageAdapter)


def test_nas_storage_backend(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("BACKUP_STORAGE_BACKEND", "nas")
    monkeypatch.setenv("BACKUP_NAS_ROOT", str(tmp_path))

    storage = get_backup_storage()

    assert isinstance(storage, NasStorageAdapter)


def test_unknown_storage_backend_rejected(monkeypatch):
    monkeypatch.setenv("BACKUP_STORAGE_BACKEND", "invalid")

    with pytest.raises(RuntimeError):
        get_backup_storage()


def test_storage_rejects_delete_outside_root(tmp_path: Path):
    root = tmp_path / "backups"
    root.mkdir()

    outside = tmp_path / "outside.dump"
    outside.write_text("do not delete", encoding="utf-8")

    storage = LocalStorageAdapter(str(root))

    with pytest.raises(RuntimeError):
        storage.delete(outside)

    assert outside.exists()


def test_storage_health_probe(monkeypatch, tmp_path: Path):
    from app.services.backup_storage import probe_backup_storage

    monkeypatch.setenv("BACKUP_STORAGE_BACKEND", "local")
    monkeypatch.setenv("BACKUP_STORAGE_ROOT", str(tmp_path))

    result = probe_backup_storage()

    assert result["healthy"] is True
    assert result["readable"] is True
    assert result["writable"] is True


def test_storage_health_probe_does_not_expose_os_error(
    monkeypatch,
    tmp_path: Path,
):
    from unittest.mock import patch

    from app.services.backup_storage import probe_backup_storage

    monkeypatch.setenv("BACKUP_STORAGE_BACKEND", "local")
    monkeypatch.setenv("BACKUP_STORAGE_ROOT", str(tmp_path))

    secret = "SECRET_PATH_DO_NOT_EXPOSE"

    with patch.object(
        Path,
        "write_text",
        side_effect=OSError(secret),
    ):
        result = probe_backup_storage()

    assert result["healthy"] is False
    assert result["readable"] is False
    assert result["writable"] is False
    assert result["error"] == "backup_storage_unavailable"
    assert secret not in str(result)
