from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.config import get_settings
from app.db.session import get_db
from app.models.core import User
from app.services.audit import append_audit
from app.services.mikrotik import (
    MikroTikConfigurationError,
    MikroTikDisabledError,
    MikroTikError,
    MikroTikClient,
)

router = APIRouter(
    prefix="/api/v1/mikrotik",
    tags=["mikrotik"],
)

INTERFACE_RE = re.compile(r"^[A-Za-z0-9_.:+-]{1,64}$")


class DhcpRenewRequest(BaseModel):
    interface: str = Field(min_length=1, max_length=64)


def _client() -> MikroTikClient:
    try:
        return MikroTikClient()
    except MikroTikDisabledError as exc:
        raise HTTPException(
            status_code=503,
            detail="mikrotik_disabled",
        ) from exc
    except MikroTikConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


@router.get("/status")
def mikrotik_status(
    _context=Depends(require_permission("network.read")),
):
    with _client() as client:
        try:
            return client.status()
        except MikroTikError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc


@router.get("/snapshot")
def mikrotik_snapshot(
    _context=Depends(require_permission("network.read")),
):
    with _client() as client:
        try:
            return client.snapshot().as_dict()
        except MikroTikError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc


@router.post("/actions/dhcp-renew")
def renew_dhcp(
    payload: DhcpRenewRequest,
    context=Depends(require_permission("network.execute")),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if not settings.mikrotik_allow_write:
        raise HTTPException(
            status_code=403,
            detail="mikrotik_write_disabled",
        )

    if not INTERFACE_RE.fullmatch(payload.interface):
        raise HTTPException(
            status_code=422,
            detail="invalid_interface",
        )

    workspace, _membership = context

    with _client() as client:
        try:
            result = client.renew_dhcp(
                payload.interface
            )
        except MikroTikError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc

    append_audit(
        db,
        action="mikrotik.dhcp_renew",
        actor_id=str(user.id),
        organization_id=workspace.organization_id,
        workspace_id=workspace.id,
        target_type="mikrotik",
        target_id=payload.interface,
        details={
            "interface": payload.interface,
        },
    )
    db.commit()

    return {
        **result,
        "status": "requested",
    }
