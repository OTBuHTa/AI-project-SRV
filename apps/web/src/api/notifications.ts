import {
  apiJson,
  bearerHeaders,
} from './http'

export type NotificationDeliveryHealthCounts = {
  total: number
  pending: number
  sending: number
  delivered: number
  failed: number
  canceled: number
  retryable_failed: number
  exhausted_failed: number
  stale_sending: number
}

export type NotificationDeliveryHealth = {
  status: string
  issues: string[]
  observed_at: string
  claim_timeout_seconds: number
  total: NotificationDeliveryHealthCounts
  backup: NotificationDeliveryHealthCounts
  agent_lifecycle: NotificationDeliveryHealthCounts
}

export type NotificationDelivery = {
  id: string
  source: string
  workspace_id: string
  alert_event_id: string
  channel: string
  destination_id: string | null
  status: string
  attempts: number
  max_attempts: number
  next_attempt_at: string | null
  last_attempt_at: string | null
  delivered_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
}

export type NotificationDeliveryPage = {
  items: NotificationDelivery[]
  next_cursor: string | null
  has_more: boolean
  observed_at: string
}

export function getNotificationDeliveryHealth(
  accessToken: string,
) {
  return apiJson<NotificationDeliveryHealth>(
    '/api/v1/notifications/deliveries/health',
    {
      headers: bearerHeaders(accessToken),
    },
  )
}

export function getNotificationDeliveries(
  accessToken: string,
  limit = 50,
) {
  return apiJson<NotificationDeliveryPage>(
    `/api/v1/notifications/deliveries/page?limit=${limit}`,
    {
      headers: bearerHeaders(accessToken),
    },
  )
}
