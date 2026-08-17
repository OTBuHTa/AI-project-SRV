import {
  apiJson,
  bearerHeaders,
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

export function sendChat(
  accessToken: string,
  message: string,
  resourceId?: string,
  conversationId?: string | null,
) {
  return apiJson<ChatResponse>(
    '/api/v1/ai/chat',
    {
      method: 'POST',
      headers: {
        ...bearerHeaders(accessToken),
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
