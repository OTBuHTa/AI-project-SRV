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
from app.models.core import BackupArtifact, BackupJob, BackupSchedule
from app.schemas.backups import BackupCreate, BackupJobOut
from app.schemas.backup_schedule import BackupScheduleOut, BackupScheduleUpdate
from app.schemas.backup_health import BackupCleanupOut, BackupCleanupRequest, BackupHealthOut, BackupStorageHealthOut
from app.services.backup import BackupError
from app.services.backup_execution import (
    create_backup_job,
    execute_backup_job,
    fail_backup_job,
)
from app.services.backup_cleanup import cleanup_expired_backups
from app.services.backup_health import evaluate_backup_health
from app.services.backup_retention import RetentionPolicy
from app.services.backup_scheduler import calculate_next_run
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

    job = create_backup_job(
        db,
        workspace_id=str(workspace.id),
        backup_type=payload.backup_type,
    )

    try:
        return execute_backup_job(
            db,
            job=job,
        )

    except (BackupError, BackupVerificationError) as exc:
        fail_backup_job(
            db,
            job=job,
            error=exc,
        )

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


@router.get("/schedule", response_model=BackupScheduleOut | None)
def get_backup_schedule(
    context=Depends(require_permission("workspace.read")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context

    return db.scalar(
        select(BackupSchedule).where(
            BackupSchedule.workspace_id == str(workspace.id)
        )
    )


@router.put("/schedule", response_model=BackupScheduleOut)
def update_backup_schedule(
    payload: BackupScheduleUpdate,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    workspace_id = str(workspace.id)

    schedule = db.scalar(
        select(BackupSchedule).where(
            BackupSchedule.workspace_id == workspace_id
        )
    )

    if schedule is None:
        schedule = BackupSchedule(
            workspace_id=workspace_id,
        )
        db.add(schedule)

    schedule.enabled = payload.enabled
    schedule.interval_minutes = payload.interval_minutes
    schedule.retention_keep_last = payload.retention_keep_last
    schedule.retention_max_age_days = payload.retention_max_age_days

    if schedule.enabled:
        schedule.next_run_at = calculate_next_run(
            interval_minutes=schedule.interval_minutes,
        )
    else:
        schedule.next_run_at = None

    db.commit()
    db.refresh(schedule)

    return schedule
