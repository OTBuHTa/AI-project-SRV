import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.audit import router as audit_router
from app.api.v1.agents import router as agents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.ai_tools import router as ai_tools_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.actions import router as actions_router
from app.api.v1.ai_actions import router as ai_actions_router
from app.api.v1.workspaces import router as workspaces_router
from app.core.config import get_settings
from app.middleware.request_context import RequestContextMiddleware
from app.db.session import SessionLocal
from app.services.agent_status import evaluate_agent_statuses
from app.api.v1.backups import router as backups_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.inventory import router as inventory_router

settings = get_settings()

async def _status_loop():
    while True:
        try:
            with SessionLocal() as db:
                evaluate_agent_statuses(db)
        except Exception:
            pass
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_status_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(title=settings.app_name, version="0.1.16-alpha", lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(audit_router)
app.include_router(agents_router)
app.include_router(monitoring_router)
app.include_router(ai_tools_router)
app.include_router(assistant_router)
app.include_router(actions_router)
app.include_router(ai_actions_router)
app.include_router(backups_router)
app.include_router(notifications_router)
app.include_router(inventory_router)


@app.get("/api/v1")
def api_root():
    return {
        "name": settings.app_name,
        "version": "0.1.16-alpha",
        "phase": "Infrastructure Inventory + Lifecycle",
    }
