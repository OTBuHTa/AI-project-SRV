from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.backup_cleanup import cleanup_expired_backups
from app.services.backup_retention import RetentionPolicy


@dataclass
class Artifact:
    id: str
    created_at: datetime
    storage_uri: str | None


class FakeSession:
    def __init__(self):
        self.deleted = []
        self.committed = False
        self.rolled_back = False

    def delete(self, item):
        self.deleted.append(item)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_cleanup_removes_expired_artifact(tmp_path: Path, monkeypatch):
    now = datetime.now(timezone.utc)

    backup_root = tmp_path / "backups"
    backup_root.mkdir()

    monkeypatch.setenv("BACKUP_STORAGE_BACKEND", "local")
    monkeypatch.setenv("BACKUP_STORAGE_ROOT", str(backup_root))

    recent = Artifact(
        id="recent",
        created_at=now,
        storage_uri=None,
    )

    old_file = backup_root / "old.dump"
    old_file.write_text("backup", encoding="utf-8")

    old = Artifact(
        id="old",
        created_at=now - timedelta(days=40),
        storage_uri=str(old_file),
    )

    session = FakeSession()

    result = cleanup_expired_backups(
        session,
        [recent, old],
        RetentionPolicy(
            keep_last=1,
            max_age_days=30,
        ),
    )

    assert result["deleted_files"] == 1
    assert result["deleted_records"] == 1
    assert not old_file.exists()
    assert session.deleted == [old]
    assert session.committed is True
    assert session.rolled_back is False
