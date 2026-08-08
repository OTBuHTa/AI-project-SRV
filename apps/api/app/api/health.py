from fastapi import APIRouter, HTTPException
from redis import Redis
from sqlalchemy import text
from app.core.config import get_settings
from app.db.session import engine

router = APIRouter(tags=["system"])
settings = get_settings()


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@router.get("/ready")
def ready():
    checks = {"database": False, "redis": False}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        checks["redis"] = bool(Redis.from_url(settings.redis_url).ping())
    except Exception:
        pass
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}
