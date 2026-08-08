from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.services.backup_retention import (
    RetentionPolicy,
    select_artifacts_to_delete,
)


@dataclass
class Artifact:
    id: str
    created_at: datetime


def test_retention_keeps_recent_artifacts():
    now = datetime.now(timezone.utc)

    artifacts = [
        Artifact(
            id=str(i),
            created_at=now - timedelta(days=i),
        )
        for i in range(10)
    ]

    policy = RetentionPolicy(
        keep_last=3,
        max_age_days=5,
    )

    expired = select_artifacts_to_delete(
        artifacts,
        policy,
        now=now,
    )

    assert {item.id for item in expired} == {
        "6",
        "7",
        "8",
        "9",
    }
