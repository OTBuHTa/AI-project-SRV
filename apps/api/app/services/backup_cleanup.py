from sqlalchemy.orm import Session

from app.models.core import BackupArtifact
from app.services.backup_retention import RetentionPolicy, select_artifacts_to_delete
from app.services.backup_storage import get_backup_storage


class BackupCleanupError(RuntimeError):
    pass


def cleanup_expired_backups(
    db: Session,
    artifacts: list[BackupArtifact],
    policy: RetentionPolicy,
) -> dict:
    expired = select_artifacts_to_delete(
        artifacts,
        policy,
    )

    storage = get_backup_storage()

    deleted_files = 0
    deleted_records = 0
    errors: list[str] = []

    for artifact in expired:
        if artifact.storage_uri:
            try:
                deleted = storage.delete(artifact.storage_uri)

                if deleted:
                    deleted_files += 1
            except Exception as exc:
                errors.append(f"{artifact.id}: {exc}")
                continue

        db.delete(artifact)
        deleted_records += 1

    if errors:
        db.rollback()
        raise BackupCleanupError("; ".join(errors))

    db.commit()

    return {
        "deleted_files": deleted_files,
        "deleted_records": deleted_records,
    }
