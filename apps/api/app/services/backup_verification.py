import os
import subprocess
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import make_url


class BackupVerificationError(RuntimeError):
    pass


def _postgres_connection(database_url: str) -> dict:
    url = make_url(database_url)

    if not url.drivername.startswith("postgresql"):
        raise BackupVerificationError(
            f"unsupported database driver: {url.drivername}"
        )

    return {
        "host": url.host or "postgres",
        "port": str(url.port or 5432),
        "user": url.username or "postgres",
        "password": url.password or "",
        "database": url.database or "postgres",
    }


def _postgres_env(connection: dict) -> dict:
    env = os.environ.copy()

    if connection["password"]:
        env["PGPASSWORD"] = connection["password"]

    return env


def _psql_scalar(
    connection: dict,
    *,
    database: str,
    query: str,
) -> str:
    result = subprocess.run(
        [
            "psql",
            "-h",
            connection["host"],
            "-p",
            connection["port"],
            "-U",
            connection["user"],
            "-d",
            database,
            "-Atqc",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=_postgres_env(connection),
    )

    return result.stdout.strip()


def verify_postgres_archive(path: Path) -> dict:
    path = Path(path)

    if not path.is_file():
        raise BackupVerificationError(
            f"backup archive does not exist: {path}"
        )

    try:
        subprocess.run(
            ["pg_restore", "--list", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise BackupVerificationError(
            f"backup archive is unreadable: {path}"
        ) from exc

    return {
        "valid": True,
        "archive_readable": True,
    }


def verify_postgres_restore(
    path: Path,
    *,
    database_url: str,
    min_public_tables: int = 1,
) -> dict:
    path = Path(path)

    verify_postgres_archive(path)

    connection = _postgres_connection(database_url)

    try:
        expected_revision = _psql_scalar(
            connection,
            database=connection["database"],
            query="SELECT version_num FROM alembic_version LIMIT 1",
        )
    except subprocess.CalledProcessError as exc:
        raise BackupVerificationError(
            "unable to read source Alembic revision"
        ) from exc

    if not expected_revision:
        raise BackupVerificationError(
            "source database has no Alembic revision"
        )

    restore_database = f"aisrv_restore_{uuid4().hex[:12]}"

    create_command = [
        "createdb",
        "-h",
        connection["host"],
        "-p",
        connection["port"],
        "-U",
        connection["user"],
        restore_database,
    ]

    drop_command = [
        "dropdb",
        "--if-exists",
        "-h",
        connection["host"],
        "-p",
        connection["port"],
        "-U",
        connection["user"],
        restore_database,
    ]

    env = _postgres_env(connection)

    try:
        subprocess.run(
            create_command,
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

        subprocess.run(
            [
                "pg_restore",
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                "-h",
                connection["host"],
                "-p",
                connection["port"],
                "-U",
                connection["user"],
                "-d",
                restore_database,
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )

        restored_revision = _psql_scalar(
            connection,
            database=restore_database,
            query="SELECT version_num FROM alembic_version LIMIT 1",
        )

        table_count_raw = _psql_scalar(
            connection,
            database=restore_database,
            query=(
                "SELECT count(*) "
                "FROM pg_tables "
                "WHERE schemaname = 'public'"
            ),
        )

        table_count = int(table_count_raw)

        if restored_revision != expected_revision:
            raise BackupVerificationError(
                "restored Alembic revision mismatch: "
                f"expected {expected_revision}, "
                f"got {restored_revision}"
            )

        if table_count < min_public_tables:
            raise BackupVerificationError(
                "restored database contains too few public tables: "
                f"{table_count} < {min_public_tables}"
            )

        return {
            "valid": True,
            "archive_readable": True,
            "restore_verified": True,
            "alembic_revision": restored_revision,
            "public_table_count": table_count,
        }

    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()

        raise BackupVerificationError(
            f"PostgreSQL restore verification failed: {stderr}"
        ) from exc

    finally:
        subprocess.run(
            drop_command,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
