import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import has_permission
from app.core.security import decode_token
from app.db.session import get_db
from app.models.core import Membership, User, UserStatus, Workspace

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
    try:
        claims = decode_token(credentials.credentials)
        if claims.get("typ") != "access":
            raise ValueError("wrong token type")
        user_id = uuid.UUID(claims["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token") from None

    user = db.get(User, user_id)
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="inactive_user")
    return user


def get_workspace_membership(
    x_workspace_id: uuid.UUID = Header(alias="X-Workspace-ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[Workspace, Membership]:
    workspace = db.get(Workspace, x_workspace_id)
    membership = db.scalar(
        select(Membership).where(
            Membership.workspace_id == x_workspace_id,
            Membership.user_id == user.id,
        )
    )
    if not workspace or not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workspace_not_found")
    return workspace, membership


def require_permission(permission: str) -> Callable:
    def dependency(
        context: tuple[Workspace, Membership] = Depends(get_workspace_membership),
    ) -> tuple[Workspace, Membership]:
        workspace, membership = context
        if not has_permission(membership.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission_denied")
        return workspace, membership

    return dependency
