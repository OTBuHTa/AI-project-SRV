from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import subprocess
import tempfile
import uuid

from app.services.backup_storage import get_backup_storage, sha256_file


@dataclass
class BackupArtifactResult:
    artifact_type: str
    source_path: str
    storage_path: str
    sha256: str
    size_bytes: int
    verified: bool


class BackupError(RuntimeError):
    pass


class BackupService:
    def __init__(
        self,
        database_url: str,
        storage_root: str,
        work_root: str | None = None,
    ):
        self.database_url = database_url.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1,
        )
        self.storage = get_backup_storage()
        self.work_root = Path(work_root or "/tmp/ai-project-srv-backups")
        self.work_root.mkdir(parents=True, exist_ok=True)

    def create_postgres_backup(
        self,
        workspace_id: str,
    ) -> BackupArtifactResult:
        backup_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        work_dir = self.work_root / backup_id
        work_dir.mkdir(parents=True, exist_ok=False)

        dump_path = work_dir / "postgres.dump"

        command = [
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--file",
            str(dump_path),
            self.database_url,
        ]

        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=300,
                shell=False,
            )
        except FileNotFoundError as exc:
            raise BackupError("pg_dump is not installed") from exc
        except subprocess.TimeoutExpired as exc:
            raise BackupError("pg_dump timed out") from exc

        if result.returncode != 0:
            raise BackupError(
                f"pg_dump failed: {result.stderr.strip()}"
            )

        if not dump_path.exists():
            raise BackupError("pg_dump completed but dump file is missing")

        digest = sha256_file(dump_path)
        size_bytes = dump_path.stat().st_size

        relative_path = (
            f"{workspace_id}/{timestamp}/{backup_id}/postgres.dump"
        )

        stored_path = self.storage.put(
            dump_path,
            relative_path,
        )

        verified = self.storage.verify(
            stored_path,
            digest,
        )

        if not verified:
            raise BackupError(
                "stored backup checksum verification failed"
            )

        manifest = {
            "backup_id": backup_id,
            "workspace_id": workspace_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "artifact_type": "postgres",
            "file": stored_path.name,
            "sha256": digest,
            "size_bytes": size_bytes,
            "checksum_verified": verified,
        }

        manifest_source = work_dir / "manifest.json"

        manifest_source.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        manifest_relative = (
            f"{workspace_id}/{timestamp}/{backup_id}/manifest.json"
        )

        self.storage.put(
            manifest_source,
            manifest_relative,
        )

        return BackupArtifactResult(
            artifact_type="postgres",
            source_path=str(dump_path),
            storage_path=str(stored_path),
            sha256=digest,
            size_bytes=size_bytes,
            verified=True,
        )
