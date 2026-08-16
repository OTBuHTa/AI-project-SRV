from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis import Redis
from redis.exceptions import RedisError
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
from app.services.auth_rate_limit import (
    account_fingerprint,
    clear_account_login_failures,
    login_rate_limit_exceeded,
    record_failed_login,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


def _auth_rate_limit_redis() -> Redis:
    return Redis.from_url(settings.redis_url)


def _login_source_ip(request: Request) -> str:
    if request.client:
        return request.client.host

    return "unknown"


def _disable_sensitive_response_caching(
    response: Response,
) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _audit_login_security_event(
    db: Session,
    request: Request,
    *,
    email: str,
    source_ip: str,
    result: str,
    reason: str,
    stage: str,
) -> None:
    append_audit(
        db,
        action="auth.login",
        result=result,
        request_id=getattr(request.state, "request_id", None),
        source_ip=source_ip,
        details={
            "account_fingerprint": account_fingerprint(email),
            "reason": reason,
            "stage": stage,
        },
    )
    db.commit()


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
def bootstrap(
    payload: BootstrapRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
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
    _disable_sensitive_response_caching(response)
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()
    source_ip = _login_source_ip(request)
    rate_limit_redis = None

    if settings.auth_rate_limit_enabled:
        rate_limit_redis = _auth_rate_limit_redis()

        try:
            limited = login_rate_limit_exceeded(
                rate_limit_redis,
                source_ip=source_ip,
                email=email,
                ip_limit=(
                    settings.auth_rate_limit_ip_attempts
                ),
                account_limit=(
                    settings.auth_rate_limit_account_attempts
                ),
            )
        except RedisError:
            _audit_login_security_event(
                db,
                request,
                email=email,
                source_ip=source_ip,
                result="error",
                reason="rate_limit_unavailable",
                stage="precheck",
            )
            raise HTTPException(
                status_code=503,
                detail="authentication_service_unavailable",
            ) from None

        if limited:
            _audit_login_security_event(
                db,
                request,
                email=email,
                source_ip=source_ip,
                result="denied",
                reason="rate_limited",
                stage="precheck",
            )
            raise HTTPException(
                status_code=429,
                detail="too_many_login_attempts",
                headers={"Retry-After": str(
                    settings.auth_rate_limit_window_seconds
                )},
            )

    user = db.scalar(
        select(User).where(User.email == email)
    )
    if not user or not verify_password(payload.password, user.password_hash):
        if rate_limit_redis is not None:
            try:
                record_failed_login(
                    rate_limit_redis,
                    source_ip=source_ip,
                    email=email,
                    window_seconds=(
                        settings.auth_rate_limit_window_seconds
                    ),
                )
            except RedisError:
                _audit_login_security_event(
                    db,
                    request,
                    email=email,
                    source_ip=source_ip,
                    result="error",
                    reason="rate_limit_unavailable",
                    stage="record_failure",
                )
                raise HTTPException(
                    status_code=503,
                    detail="authentication_service_unavailable",
                ) from None

        append_audit(
            db,
            action="auth.login",
            result="denied",
            request_id=getattr(request.state, "request_id", None),
            source_ip=source_ip,
            details={
                "account_fingerprint": account_fingerprint(email),
                "reason": "invalid_credentials",
                "stage": "credentials",
            },
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

    if rate_limit_redis is not None:
        try:
            clear_account_login_failures(
                rate_limit_redis,
                email=email,
            )
        except RedisError:
            _audit_login_security_event(
                db,
                request,
                email=email,
                source_ip=source_ip,
                result="error",
                reason="rate_limit_unavailable",
                stage="clear_account",
            )
            raise HTTPException(
                status_code=503,
                detail="authentication_service_unavailable",
            ) from None

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
    _disable_sensitive_response_caching(response)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    response: Response,
    db: Session = Depends(get_db),
):
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
    _disable_sensitive_response_caching(response)
    return tokens


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(get_current_user)):
    return user
