import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import BackupArtifact, BackupJob
from app.services.backup import BackupService
from app.services.backup_verification import verify_postgres_restore


settings = get_settings()


EXPECTED_POSTGRES_MAJOR = "16"


def verify_backup_client_version() -> None:
    result = subprocess.run(
        ["pg_dump", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    version = result.stdout.strip()

    if f" {EXPECTED_POSTGRES_MAJOR}." not in version:
        raise RuntimeError(
            "unsupported pg_dump version: "
            f"{version}; expected PostgreSQL {EXPECTED_POSTGRES_MAJOR}.x"
        )


def create_backup_job(
    db: Session,
    *,
    workspace_id: str,
    backup_type: str = "postgres",
) -> BackupJob:
    now = datetime.now(timezone.utc)

    job = BackupJob(
        id=str(uuid4()),
        workspace_id=workspace_id,
        backup_type=backup_type,
        status="running",
        started_at=now,
        created_at=now,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def execute_backup_job(
    db: Session,
    *,
    job: BackupJob,
) -> BackupJob:
    verify_backup_client_version()

    storage_root = os.getenv(
        "BACKUP_STORAGE_ROOT",
        "/var/lib/ai-project-srv/backups",
    )

    work_root = os.getenv(
        "BACKUP_WORK_ROOT",
        "/tmp/ai-project-srv-backups",
    )

    service = BackupService(
        database_url=str(settings.database_url),
        storage_root=storage_root,
        work_root=work_root,
    )

    result = service.create_postgres_backup(
        workspace_id=job.workspace_id,
    )

    restore_check = verify_postgres_restore(
        Path(result.storage_path),
        database_url=str(settings.database_url),
        min_public_tables=1,
    )

    artifact = BackupArtifact(
        id=str(uuid4()),
        backup_job_id=job.id,
        artifact_type=result.artifact_type,
        path=result.source_path,
        storage_uri=result.storage_path,
        sha256=result.sha256,
        size_bytes=result.size_bytes,
        status="verified",
        restore_verified=bool(restore_check["restore_verified"]),
        created_at=datetime.now(timezone.utc),
    )

    db.add(artifact)

    job.status = "restore_verified"
    job.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    return job


def fail_backup_job(
    db: Session,
    *,
    job: BackupJob,
    error: Exception,
) -> BackupJob:
    job.status = "failed"
    job.error = str(error)
    job.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)

    return job
