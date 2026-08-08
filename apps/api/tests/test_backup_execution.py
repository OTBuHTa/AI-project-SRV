from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.backup_execution import verify_backup_client_version


@patch("app.services.backup_execution.subprocess.run")
def test_pg_dump_16_is_accepted(run):
    run.return_value = SimpleNamespace(
        stdout="pg_dump (PostgreSQL) 16.14\n"
    )

    verify_backup_client_version()


@patch("app.services.backup_execution.subprocess.run")
def test_pg_dump_wrong_major_is_rejected(run):
    run.return_value = SimpleNamespace(
        stdout="pg_dump (PostgreSQL) 17.10\n"
    )

    with pytest.raises(RuntimeError, match="expected PostgreSQL 16"):
        verify_backup_client_version()
