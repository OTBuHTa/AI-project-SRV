from pathlib import Path
import subprocess


class BackupVerificationError(RuntimeError):
    pass


def verify_postgres_archive(path: Path) -> dict:
    if not path.exists():
        raise BackupVerificationError(
            f"backup archive does not exist: {path}"
        )

    try:
        result = subprocess.run(
            [
                "pg_restore",
                "--list",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise BackupVerificationError(
            "pg_restore is not installed"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise BackupVerificationError(
            "pg_restore verification timed out"
        ) from exc

    if result.returncode != 0:
        raise BackupVerificationError(
            f"pg_restore verification failed: {result.stderr.strip()}"
        )

    entries = [
        line
        for line in result.stdout.splitlines()
        if line and not line.startswith(";")
    ]

    if not entries:
        raise BackupVerificationError(
            "backup archive contains no restore entries"
        )

    return {
        "valid": True,
        "restore_entries": len(entries),
    }
