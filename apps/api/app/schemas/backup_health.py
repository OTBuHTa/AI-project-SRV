from datetime import datetime

from pydantic import BaseModel


class BackupHealthOut(BaseModel):
    status: str
    reason: str
    last_verified_at: datetime | None
    verified_count: int


class BackupCleanupRequest(BaseModel):
    keep_last: int = 7
    max_age_days: int = 30


class BackupCleanupOut(BaseModel):
    deleted_files: int
    deleted_records: int


class BackupStorageHealthOut(BaseModel):
    backend: str
    root: str
    writable: bool
    readable: bool
    healthy: bool
    error: str | None = None
