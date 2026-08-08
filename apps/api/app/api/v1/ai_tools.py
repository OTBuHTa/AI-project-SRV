import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.db.session import get_db
from app.models.core import Agent, Resource
from app.schemas.agents import ResourceHealthResponse
from app.services.resource_health import evaluate_resource

router=APIRouter(prefix="/api/v1/ai/tools", tags=["ai-tools"])

@router.get("/resource-health/{resource_id}", response_model=ResourceHealthResponse)
def resource_health(resource_id: uuid.UUID, context=Depends(require_permission("resource.read")), db: Session=Depends(get_db)):
    workspace,_=context
    resource=db.get(Resource, resource_id)
    if not resource or resource.workspace_id != workspace.id:
        raise HTTPException(status_code=404, detail="resource_not_found")
    agent=db.query(Agent).filter(Agent.resource_id==resource.id, Agent.revoked_at.is_(None)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="active_agent_not_found")
    assessment=evaluate_resource(agent, resource)
    return ResourceHealthResponse(
        resource_id=resource.id, hostname=resource.hostname or resource.name,
        metrics=agent.last_metrics, docker=(resource.metadata_json or {}).get("docker"),
        last_seen_at=agent.last_seen_at, **assessment,
    )
