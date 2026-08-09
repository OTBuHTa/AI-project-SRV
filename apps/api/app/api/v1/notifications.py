from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.core import (
    NotificationDestination,
    NotificationRoute,
)
from app.schemas.notifications import (
    NotificationDestinationCreate,
    NotificationDestinationOut,
    NotificationDestinationUpdate,
    NotificationRouteCreate,
    NotificationRouteOut,
    NotificationRouteUpdate,
)


router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"],
)


def _get_destination(
    db: Session,
    *,
    workspace_id: str,
    destination_id: str,
) -> NotificationDestination:
    destination = db.scalar(
        select(NotificationDestination).where(
            NotificationDestination.id == destination_id,
            NotificationDestination.workspace_id == workspace_id,
        )
    )

    if destination is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="notification_destination_not_found",
        )

    return destination


def _get_route(
    db: Session,
    *,
    workspace_id: str,
    route_id: str,
) -> NotificationRoute:
    route = db.scalar(
        select(NotificationRoute).where(
            NotificationRoute.id == route_id,
            NotificationRoute.workspace_id == workspace_id,
        )
    )

    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="notification_route_not_found",
        )

    return route


@router.get(
    "/destinations",
    response_model=list[NotificationDestinationOut],
)
def list_notification_destinations(
    context=Depends(require_permission("workspace.read")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    workspace_id = str(workspace.id)

    return db.scalars(
        select(NotificationDestination)
        .where(
            NotificationDestination.workspace_id == workspace_id
        )
        .order_by(NotificationDestination.name)
    ).all()


@router.post(
    "/destinations",
    response_model=NotificationDestinationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_notification_destination(
    payload: NotificationDestinationCreate,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    workspace_id = str(workspace.id)

    if payload.channel != "webhook":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unsupported_notification_channel",
        )

    destination = NotificationDestination(
        id=str(uuid4()),
        workspace_id=workspace_id,
        name=payload.name,
        channel=payload.channel,
        endpoint=payload.endpoint,
        enabled=payload.enabled,
    )

    db.add(destination)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="notification_destination_name_conflict",
        ) from exc

    db.refresh(destination)

    return destination


@router.patch(
    "/destinations/{destination_id}",
    response_model=NotificationDestinationOut,
)
def update_notification_destination(
    destination_id: str,
    payload: NotificationDestinationUpdate,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context

    destination = _get_destination(
        db,
        workspace_id=str(workspace.id),
        destination_id=destination_id,
    )

    if "name" in payload.model_fields_set:
        destination.name = payload.name

    if "endpoint" in payload.model_fields_set:
        destination.endpoint = payload.endpoint

    if "enabled" in payload.model_fields_set:
        destination.enabled = payload.enabled

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="notification_destination_name_conflict",
        ) from exc

    db.refresh(destination)

    return destination


@router.delete(
    "/destinations/{destination_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification_destination(
    destination_id: str,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    workspace_id = str(workspace.id)

    destination = _get_destination(
        db,
        workspace_id=workspace_id,
        destination_id=destination_id,
    )

    db.delete(destination)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/routes",
    response_model=list[NotificationRouteOut],
)
def list_notification_routes(
    context=Depends(require_permission("workspace.read")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    workspace_id = str(workspace.id)

    return db.scalars(
        select(NotificationRoute)
        .where(
            NotificationRoute.workspace_id == workspace_id
        )
        .order_by(NotificationRoute.created_at)
    ).all()


@router.post(
    "/routes",
    response_model=NotificationRouteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_notification_route(
    payload: NotificationRouteCreate,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    workspace_id = str(workspace.id)

    _get_destination(
        db,
        workspace_id=workspace_id,
        destination_id=payload.destination_id,
    )

    route = NotificationRoute(
        id=str(uuid4()),
        workspace_id=workspace_id,
        destination_id=payload.destination_id,
        alert_code=payload.alert_code,
        severity=payload.severity,
        enabled=payload.enabled,
    )

    db.add(route)
    db.commit()
    db.refresh(route)

    return route


@router.patch(
    "/routes/{route_id}",
    response_model=NotificationRouteOut,
)
def update_notification_route(
    route_id: str,
    payload: NotificationRouteUpdate,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context

    route = _get_route(
        db,
        workspace_id=str(workspace.id),
        route_id=route_id,
    )

    if "alert_code" in payload.model_fields_set:
        route.alert_code = payload.alert_code

    if "severity" in payload.model_fields_set:
        route.severity = payload.severity

    if "enabled" in payload.model_fields_set:
        route.enabled = payload.enabled

    db.commit()
    db.refresh(route)

    return route


@router.delete(
    "/routes/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification_route(
    route_id: str,
    context=Depends(require_permission("workspace.manage")),
    db: Session = Depends(get_db),
):
    workspace, _membership = context

    route = _get_route(
        db,
        workspace_id=str(workspace.id),
        route_id=route_id,
    )

    db.delete(route)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
