import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.core import Conversation, ConversationMessage, User
from app.schemas.ai import ChatRequest, ChatResponse, ConversationSummary, MessageOut
from app.services.ai_context import build_resource_context, deterministic_fallback
from app.services.audit import append_audit
from app.services.llm_gateway import LLMUnavailable, llm_gateway

router = APIRouter(prefix='/api/v1/ai', tags=['ai-assistant'])

SYSTEM_PROMPT = """You are AI-project SRV, an infrastructure operations assistant.
Rules:
- Treat provided telemetry/tool context as authoritative facts.
- Never claim that you executed a change; this release is read-only.
- Clearly separate observed facts from recommendations.
- If data is missing, say so.
- Prefer concise operational Russian unless the user uses another language.
- Do not invent commands, metrics, hosts, incidents, or successful actions.
"""

def _conversation(db: Session, workspace_id, user_id, conversation_id, message: str):
    if conversation_id:
        row = db.get(Conversation, conversation_id)
        if not row or row.workspace_id != workspace_id or row.user_id != user_id:
            raise HTTPException(status_code=404, detail='conversation_not_found')
        return row
    title = message.strip().replace('\n', ' ')[:100] or 'New conversation'
    row = Conversation(workspace_id=workspace_id, user_id=user_id, title=title)
    db.add(row)
    db.flush()
    return row

@router.post('/chat', response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    context=Depends(require_permission('resource.read')),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace, _membership = context
    conversation = _conversation(db, workspace.id, user.id, payload.conversation_id, payload.message)

    tool_context = None
    if payload.resource_id:
        tool_context = build_resource_context(db, workspace.id, payload.resource_id)
        if tool_context is None:
            raise HTTPException(status_code=404, detail='resource_not_found')

    user_row = ConversationMessage(
        conversation_id=conversation.id, role='user', content=payload.message, tool_context=tool_context
    )
    db.add(user_row)
    db.flush()

    recent = db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(12)
    ).all()
    history = []
    for row in reversed(recent):
        if row.role in {'user', 'assistant'}:
            history.append({'role': row.role, 'content': row.content})

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    if tool_context:
        messages.append({
            'role': 'system',
            'content': 'Current read-only infrastructure context (JSON):\n' + json.dumps(tool_context, default=str),
        })
    messages.extend(history)

    mode = 'llm'
    try:
        answer, model = await llm_gateway.chat(messages)
    except LLMUnavailable:
        mode = 'deterministic-fallback'
        model = 'fallback/resource-health-v1'
        answer = deterministic_fallback(payload.message, tool_context)

    assistant_row = ConversationMessage(
        conversation_id=conversation.id, role='assistant', content=answer, tool_context=tool_context
    )
    db.add(assistant_row)
    conversation.updated_at = datetime.now(UTC)
    append_audit(
        db, action='ai.chat', actor_id=str(user.id), organization_id=workspace.organization_id,
        workspace_id=workspace.id, target_type='conversation', target_id=str(conversation.id),
        details={'mode': mode, 'model': model, 'resource_id': str(payload.resource_id) if payload.resource_id else None},
    )
    db.commit()
    db.refresh(assistant_row)
    return ChatResponse(
        conversation_id=conversation.id, message_id=assistant_row.id, answer=answer, model=model,
        mode=mode, tool_context=tool_context, created_at=assistant_row.created_at,
    )

@router.get('/conversations', response_model=list[ConversationSummary])
def conversations(context=Depends(require_permission('resource.read')), user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    workspace, _ = context
    rows = db.scalars(
        select(Conversation).where(Conversation.workspace_id == workspace.id, Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    ).all()
    return [ConversationSummary(id=r.id, title=r.title, created_at=r.created_at, updated_at=r.updated_at) for r in rows]

@router.get('/conversations/{conversation_id}/messages', response_model=list[MessageOut])
def conversation_messages(conversation_id: uuid.UUID, context=Depends(require_permission('resource.read')), user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    workspace, _ = context
    conversation = db.get(Conversation, conversation_id)
    if not conversation or conversation.workspace_id != workspace.id or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail='conversation_not_found')
    rows = db.scalars(select(ConversationMessage).where(ConversationMessage.conversation_id == conversation.id).order_by(ConversationMessage.created_at)).all()
    return [MessageOut(id=r.id, role=r.role, content=r.content, tool_context=r.tool_context, created_at=r.created_at) for r in rows]
