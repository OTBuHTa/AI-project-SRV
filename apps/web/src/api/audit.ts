import {
  apiJson,
  bearerHeaders,
} from './http'

export type AuditEvent = {
  id: string
  action: string
  actor_id: string | null
  result: unknown
  target_type: string | null
  target_id: string | null
  request_id: string | null
  hash: string
  previous_hash: string | null
  created_at: string
}

export function getAuditEvents(
  accessToken: string,
  limit = 100,
) {
  return apiJson<AuditEvent[]>(
    `/api/v1/audit?limit=${limit}`,
    {
      headers: bearerHeaders(accessToken),
    },
  )
}
