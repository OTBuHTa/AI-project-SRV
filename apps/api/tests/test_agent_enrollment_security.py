from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.agents import AGENT_TOKEN_TTL, enroll_agent


def _request():
    request = MagicMock()
    request.state.request_id = "test-request"
    return request


def _payload():
    return SimpleNamespace(
        enrollment_token="enroll_test",
        hostname="srv-test",
        os_name="Linux",
        architecture="x86_64",
        agent_version="0.1.16-alpha",
        capabilities=["system.metrics.read"],
    )


def test_expired_enrollment_token_is_rejected():
    db = MagicMock()

    enrollment = SimpleNamespace(
        used_at=None,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    db.scalar.return_value = enrollment

    with pytest.raises(HTTPException) as exc:
        enroll_agent(
            payload=_payload(),
            request=_request(),
            db=db,
        )

    assert exc.value.status_code == 401
    assert (
        exc.value.detail
        == "invalid_or_expired_enrollment_token"
    )


def test_used_enrollment_token_is_rejected():
    db = MagicMock()

    enrollment = SimpleNamespace(
        used_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )

    db.scalar.return_value = enrollment

    with pytest.raises(HTTPException) as exc:
        enroll_agent(
            payload=_payload(),
            request=_request(),
            db=db,
        )

    assert exc.value.status_code == 401
    assert (
        exc.value.detail
        == "invalid_or_expired_enrollment_token"
    )


def test_agent_token_ttl_is_90_days():
    assert AGENT_TOKEN_TTL == timedelta(days=90)


def test_enrollment_select_uses_for_update():
    from app.models.core import EnrollmentToken
    from sqlalchemy import select

    query = (
        select(EnrollmentToken)
        .where(EnrollmentToken.token_hash == "hash")
        .with_for_update()
    )

    sql = str(query).upper()

    assert "FOR UPDATE" in sql
