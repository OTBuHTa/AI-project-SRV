from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models.core import Membership, Organization, RefreshSession, Role, User, Workspace
from app.schemas.auth import (
    BootstrapRequest,
    CurrentUserResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.audit import append_audit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


def _issue_session(db: Session, user: User, workspace_id=None) -> TokenResponse:
    raw_refresh, token_hash = new_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)
    db.add(RefreshSession(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    return TokenResponse(
        access_token=create_access_token(user.id, workspace_id),
        refresh_token=raw_refresh,
        expires_in=settings.access_token_minutes * 60,
    )


@router.post("/bootstrap", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def bootstrap(payload: BootstrapRequest, request: Request, db: Session = Depends(get_db)):
    if not settings.bootstrap_enabled:
        raise HTTPException(status_code=404, detail="not_found")
    if db.scalar(select(func.count()).select_from(User)) > 0:
        raise HTTPException(status_code=409, detail="bootstrap_already_completed")

    user = User(
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(user)
    db.flush()
    organization = Organization(
        name=payload.organization_name,
        slug=payload.organization_slug,
        owner_user_id=user.id,
    )
    db.add(organization)
    db.flush()
    workspace = Workspace(organization_id=organization.id, name=payload.workspace_name)
    db.add(workspace)
    db.flush()
    db.add(Membership(user_id=user.id, workspace_id=workspace.id, role=Role.ORGANIZATION_OWNER.value))
    tokens = _issue_session(db, user, workspace.id)
    append_audit(
        db,
        action="platform.bootstrap",
        actor_id=str(user.id),
        organization_id=organization.id,
        workspace_id=workspace.id,
        request_id=getattr(request.state, "request_id", None),
        source_ip=request.client.host if request.client else None,
    )
    db.commit()
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        append_audit(
            db,
            action="auth.login",
            result="denied",
            request_id=getattr(request.state, "request_id", None),
            source_ip=request.client.host if request.client else None,
            details={"email": str(payload.email).lower()},
        )
        db.commit()
        raise HTTPException(status_code=401, detail="invalid_credentials")

    if payload.workspace_id:
        membership = db.scalar(
            select(Membership).where(
                Membership.user_id == user.id,
                Membership.workspace_id == payload.workspace_id,
            )
        )
        if not membership:
            raise HTTPException(status_code=404, detail="workspace_not_found")

    user.last_login_at = datetime.now(UTC)
    tokens = _issue_session(db, user, payload.workspace_id)
    append_audit(
        db,
        action="auth.login",
        actor_id=str(user.id),
        workspace_id=payload.workspace_id,
        request_id=getattr(request.state, "request_id", None),
        source_ip=request.client.host if request.client else None,
    )
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == token_hash))
    if not session or session.revoked_at or session.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=401, detail="invalid_refresh_token")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="invalid_refresh_token")
    if payload.workspace_id:
        membership = db.scalar(
            select(Membership).where(
                Membership.user_id == user.id,
                Membership.workspace_id == payload.workspace_id,
            )
        )
        if not membership:
            raise HTTPException(status_code=404, detail="workspace_not_found")

    session.revoked_at = datetime.now(UTC)
    tokens = _issue_session(db, user, payload.workspace_id)
    db.commit()
    return tokens


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(get_current_user)):
    return user
