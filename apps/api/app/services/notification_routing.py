from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.core import (
    BackupAlertEvent,
    NotificationDestination,
    NotificationRoute,
)


def find_matching_destinations(
    db: Session,
    *,
    event: BackupAlertEvent,
) -> list[NotificationDestination]:
    destinations = list(
        db.scalars(
            select(NotificationDestination)
            .join(
                NotificationRoute,
                NotificationRoute.destination_id
                == NotificationDestination.id,
            )
            .where(
                NotificationRoute.workspace_id == event.workspace_id,
                NotificationRoute.enabled.is_(True),
                NotificationDestination.workspace_id == event.workspace_id,
                NotificationDestination.enabled.is_(True),
                or_(
                    NotificationRoute.alert_code.is_(None),
                    NotificationRoute.alert_code == event.code,
                ),
                or_(
                    NotificationRoute.severity.is_(None),
                    NotificationRoute.severity == event.severity,
                ),
            )
            .distinct()
        ).all()
    )

    return destinations
