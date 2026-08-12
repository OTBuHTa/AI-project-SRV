import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class EnrollmentTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    agent_type: str = Field(default="linux", pattern=r"^[a-z0-9_-]{2,32}$")
    ttl_minutes: int = Field(default=30, ge=5, le=1440)


class EnrollmentTokenResponse(BaseModel):
    token: str
    expires_at: datetime


class AgentEnrollRequest(BaseModel):
    enrollment_token: str
    hostname: str = Field(min_length=1, max_length=255)
    agent_version: str = Field(min_length=1, max_length=64)
    os_name: str = Field(min_length=1, max_length=120)
    architecture: str = Field(min_length=1, max_length=64)
    capabilities: list[str] = Field(default_factory=list, max_length=128)


class AgentEnrollResponse(BaseModel):
    agent_id: uuid.UUID
    resource_id: uuid.UUID
    agent_token: str
    agent_token_expires_at: datetime
    heartbeat_interval_seconds: int = 30


class AgentTokenRotateResponse(BaseModel):
    agent_id: uuid.UUID
    agent_token: str
    agent_token_expires_at: datetime
    token_rotated_at: datetime


class AgentRevokeResponse(BaseModel):
    agent_id: uuid.UUID
    revoked_at: datetime
    status: str = "revoked"


class SystemMetrics(BaseModel):
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    disk_percent: float = Field(ge=0, le=100)
    disk_free_bytes: int = Field(ge=0)
    uptime_seconds: int = Field(ge=0)
    load_1m: float | None = Field(default=None, ge=0)


class DockerSummary(BaseModel):
    available: bool = False
    containers_total: int = Field(default=0, ge=0)
    containers_running: int = Field(default=0, ge=0)
    containers_stopped: int = Field(default=0, ge=0)
    containers: list[dict] = Field(default_factory=list, max_length=256)


class AgentHeartbeatRequest(BaseModel):
    status: str = Field(default="healthy", pattern=r"^(healthy|degraded)$")
    agent_version: str = Field(min_length=1, max_length=64)
    capabilities: list[str] = Field(default_factory=list, max_length=128)
    metrics: SystemMetrics
    docker: DockerSummary | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    hostname: str
    agent_type: str
    version: str
    status: str
    last_seen_at: datetime | None
    capabilities: list[str]
    metrics: dict | None


class TelemetryPoint(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    disk_free_bytes: int
    uptime_seconds: int
    load_1m: float | None
    docker: dict | None


class ResourceHealthResponse(BaseModel):
    resource_id: uuid.UUID
    hostname: str
    status: str
    health_score: int
    severity: str
    findings: list[str]
    metrics: dict | None
    docker: dict | None
    last_seen_at: datetime | None
