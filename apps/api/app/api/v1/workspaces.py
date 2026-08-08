from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.core import Membership, User, Workspace
from app.schemas.workspace import WorkspaceResponse

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Workspace, Membership.role)
        .join(Membership, Membership.workspace_id == Workspace.id)
        .where(Membership.user_id == user.id)
        .order_by(Workspace.name)
    ).all()
    return [
        WorkspaceResponse(
            id=workspace.id,
            organization_id=workspace.organization_id,
            name=workspace.name,
            environment=workspace.environment,
            status=workspace.status,
            role=role,
        )
        for workspace, role in rows
    ]


@router.get("/current", response_model=WorkspaceResponse)
def current_workspace(
    context=Depends(require_permission("workspace.read")),
):
    workspace, membership = context
    return WorkspaceResponse(
        id=workspace.id,
        organization_id=workspace.organization_id,
        name=workspace.name,
        environment=workspace.environment,
        status=workspace.status,
        role=membership.role,
    )
