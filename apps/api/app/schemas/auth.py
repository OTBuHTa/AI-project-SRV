import uuid
from pydantic import BaseModel, EmailStr, Field


class BootstrapRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, max_length=160)
    organization_name: str = Field(min_length=2, max_length=160)
    organization_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,158}[a-z0-9]$")
    workspace_name: str = Field(default="Main", min_length=1, max_length=160)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    workspace_id: uuid.UUID | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
    workspace_id: uuid.UUID | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str | None
    status: str
