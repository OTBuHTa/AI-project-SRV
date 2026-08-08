import uuid
from pydantic import BaseModel


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    environment: str
    status: str
    role: str
