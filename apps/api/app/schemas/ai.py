import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: uuid.UUID | None = None
    resource_id: uuid.UUID | None = None

class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    model: str
    mode: str
    tool_context: dict | None = None
    created_at: datetime

class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    tool_context: dict | None
    created_at: datetime
