import {
  apiJson,
  workspaceHeaders,
} from './http'

export type ChatResponse = {
  conversation_id: string
  message_id: string
  answer: string
  model: string
  mode: string
  tool_context: Record<string, unknown> | null
  created_at: string
}

export type ConversationSummary = {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type ConversationMessage = {
  id: string
  role: string
  content: string
  tool_context: Record<string, unknown> | null
  created_at: string
}

export function sendChat(
  accessToken: string,
  workspaceId: string,
  message: string,
  resourceId?: string,
  conversationId?: string | null,
) {
  return apiJson<ChatResponse>(
    '/api/v1/ai/chat',
    {
      method: 'POST',
      headers: {
        ...workspaceHeaders(
          accessToken,
          workspaceId,
        ),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id:
          conversationId ?? null,
        resource_id:
          resourceId || null,
      }),
    },
  )
}

export function getConversations(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<ConversationSummary[]>(
    '/api/v1/ai/conversations',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getConversationMessages(
  accessToken: string,
  workspaceId: string,
  conversationId: string,
) {
  return apiJson<ConversationMessage[]>(
    `/api/v1/ai/conversations/${conversationId}/messages`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}
