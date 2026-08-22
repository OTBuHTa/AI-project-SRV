import {
  apiJson,
  workspaceHeaders,
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

export type NotificationDeliveryProblem =
  NotificationDelivery & {
    problem: string
  }

export type NotificationDeliveryProblemPage = {
  items: NotificationDeliveryProblem[]
  next_cursor: string | null
  has_more: boolean
  observed_at: string
}

export type NotificationDeliveryCount = {
  total: number
  backup: number
  agent_lifecycle: number
}

export type NotificationDestination = {
  id: string
  workspace_id: string
  name: string
  channel: string
  endpoint: string
  enabled: boolean
  created_at: string
  updated_at: string
}

export type NotificationRoute = {
  id: string
  workspace_id: string
  destination_id: string
  alert_code: string | null
  severity: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export function getNotificationDeliveryHealth(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<NotificationDeliveryHealth>(
    '/api/v1/notifications/deliveries/health',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getNotificationDeliveries(
  accessToken: string,
  workspaceId: string,
  limit = 50,
) {
  return apiJson<NotificationDeliveryPage>(
    `/api/v1/notifications/deliveries/page?limit=${limit}`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getNotificationDeliveryProblems(
  accessToken: string,
  workspaceId: string,
  limit = 50,
) {
  return apiJson<NotificationDeliveryProblemPage>(
    `/api/v1/notifications/deliveries/problems/page?limit=${limit}`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getNotificationDeliveryProblemCount(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<NotificationDeliveryCount>(
    '/api/v1/notifications/deliveries/problems/count',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getNotificationDestinations(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<NotificationDestination[]>(
    '/api/v1/notifications/destinations',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getNotificationRoutes(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<NotificationRoute[]>(
    '/api/v1/notifications/routes',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}
