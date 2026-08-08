from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.config import get_settings
from app.db.session import get_db
from app.models.core import BackupArtifact, BackupJob
from app.schemas.backups import BackupCreate, BackupJobOut
from app.schemas.backup_health import BackupCleanupOut, BackupCleanupRequest, BackupHealthOut, BackupStorageHealthOut
from app.services.backup import BackupError, BackupService
from app.services.backup_cleanup import cleanup_expired_backups
from app.services.backup_health import evaluate_backup_health
from app.services.backup_retention import RetentionPolicy
from app.services.backup_storage import probe_backup_storage
from app.services.backup_verification import (
    BackupVerificationError,
    verify_postgres_archive,
)

settings = get_settings()

router = APIRouter(prefix="/api/v1/backups", tags=["backups"])


@router.get("", response_model=list[BackupJobOut])
def list_backups(
    context=Depends(require_permission("workspace.read")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context

    return db.scalars(
        select(BackupJob)
        .where(BackupJob.workspace_id == str(workspace.id))
        .order_by(BackupJob.created_at.desc())
    ).all()


@router.post("", response_model=BackupJobOut)
def create_backup(
    payload: BackupCreate,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    now = datetime.now(timezone.utc)

    job = BackupJob(
        id=str(uuid4()),
        workspace_id=str(workspace.id),
        backup_type=payload.backup_type,
        status="running",
        started_at=now,
        created_at=now,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

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

    try:
        result = service.create_postgres_backup(
            workspace_id=str(workspace.id),
        )

        restore_check = verify_postgres_archive(
            Path(result.storage_path)
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
            restore_verified=bool(restore_check["valid"]),
            created_at=datetime.now(timezone.utc),
        )

        db.add(artifact)

        job.status = "restore_verified"
        job.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job)

        return job

    except (BackupError, BackupVerificationError) as exc:
        job.status = "failed"
        job.error = str(exc)
        job.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job)

        raise HTTPException(
            status_code=500,
            detail=f"Backup failed: {exc}",
        ) from exc


@router.get("/health", response_model=BackupHealthOut)
def backup_health(
    context=Depends(require_permission("workspace.read")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context

    artifacts = db.scalars(
        select(BackupArtifact)
        .join(
            BackupJob,
            BackupArtifact.backup_job_id == BackupJob.id,
        )
        .where(BackupJob.workspace_id == str(workspace.id))
        .order_by(BackupArtifact.created_at.desc())
    ).all()

    return evaluate_backup_health(artifacts)


@router.post("/cleanup", response_model=BackupCleanupOut)
def cleanup_backups(
    payload: BackupCleanupRequest,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context

    artifacts = db.scalars(
        select(BackupArtifact)
        .join(
            BackupJob,
            BackupArtifact.backup_job_id == BackupJob.id,
        )
        .where(BackupJob.workspace_id == str(workspace.id))
        .order_by(BackupArtifact.created_at.desc())
    ).all()

    return cleanup_expired_backups(
        db,
        artifacts,
        RetentionPolicy(
            keep_last=payload.keep_last,
            max_age_days=payload.max_age_days,
        ),
    )


@router.get("/storage-health", response_model=BackupStorageHealthOut)
def backup_storage_health(
    _context=Depends(require_permission("workspace.read")),
):
    return probe_backup_storage()
