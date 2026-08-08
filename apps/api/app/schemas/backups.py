from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BackupCreate(BaseModel):
    backup_type: str = "full"


class BackupArtifactOut(BaseModel):
    id: str
    artifact_type: str
    path: str
    storage_uri: Optional[str] = None
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    status: str
    restore_verified: bool


class BackupJobOut(BaseModel):
    id: str
    workspace_id: str
    backup_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime
