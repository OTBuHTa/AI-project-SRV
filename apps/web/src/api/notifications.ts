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

export type NotificationDeliveryFilters = {
  source?: 'backup' | 'agent_lifecycle'
  status?:
    | 'pending'
    | 'sending'
    | 'delivered'
    | 'failed'
    | 'canceled'
  problem?:
    | 'retryable_failed'
    | 'exhausted_failed'
    | 'stale_sending'
  destination_id?: string
  channel?: string
  cursor?: string
}

function deliverySearchParams(
  filters: NotificationDeliveryFilters,
) {
  const params = new URLSearchParams()

  if (filters.source) {
    params.set('source', filters.source)
  }

  if (filters.destination_id) {
    params.set(
      'destination_id',
      filters.destination_id,
    )
  }

  if (filters.channel) {
    params.set('channel', filters.channel)
  }

  return params
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
  filters: NotificationDeliveryFilters = {},
  limit = 50,
) {
  const params = deliverySearchParams(filters)

  if (filters.status) {
    params.set('status', filters.status)
  }

  if (filters.cursor) {
    params.set('cursor', filters.cursor)
  }

  params.set('limit', String(limit))

  return apiJson<NotificationDeliveryPage>(
    `/api/v1/notifications/deliveries/page?${params.toString()}`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getNotificationDeliveryCount(
  accessToken: string,
  workspaceId: string,
  filters: NotificationDeliveryFilters = {},
) {
  const params = deliverySearchParams(filters)

  if (filters.status) {
    params.set('status', filters.status)
  }

  const query = params.toString()

  return apiJson<NotificationDeliveryCount>(
    `/api/v1/notifications/deliveries/count${query ? `?${query}` : ''}`,
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
  filters: NotificationDeliveryFilters = {},
  limit = 50,
) {
  const params = deliverySearchParams(filters)

  if (filters.problem) {
    params.set('problem', filters.problem)
  }

  if (filters.cursor) {
    params.set('cursor', filters.cursor)
  }

  params.set('limit', String(limit))

  return apiJson<NotificationDeliveryProblemPage>(
    `/api/v1/notifications/deliveries/problems/page?${params.toString()}`,
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
  filters: NotificationDeliveryFilters = {},
) {
  const params = deliverySearchParams(filters)

  if (filters.problem) {
    params.set('problem', filters.problem)
  }

  const query = params.toString()

  return apiJson<NotificationDeliveryCount>(
    `/api/v1/notifications/deliveries/problems/count${query ? `?${query}` : ''}`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}


export type NotificationDestinationCreate = {
  name: string
  channel: 'webhook'
  endpoint: string
  enabled: boolean
}

export type NotificationDestinationUpdate = {
  name?: string
  endpoint?: string
  enabled?: boolean
}

export function createNotificationDestination(
  accessToken: string,
  workspaceId: string,
  payload: NotificationDestinationCreate,
) {
  return apiJson<NotificationDestination>(
    '/api/v1/notifications/destinations',
    {
      method: 'POST',
      headers: {
        ...workspaceHeaders(
          accessToken,
          workspaceId,
        ),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export function updateNotificationDestination(
  accessToken: string,
  workspaceId: string,
  destinationId: string,
  payload: NotificationDestinationUpdate,
) {
  return apiJson<NotificationDestination>(
    `/api/v1/notifications/destinations/${destinationId}`,
    {
      method: 'PATCH',
      headers: {
        ...workspaceHeaders(
          accessToken,
          workspaceId,
        ),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export function deleteNotificationDestination(
  accessToken: string,
  workspaceId: string,
  destinationId: string,
) {
  return apiJson<void>(
    `/api/v1/notifications/destinations/${destinationId}`,
    {
      method: 'DELETE',
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


export type NotificationRouteCreate = {
  destination_id: string
  alert_code: string | null
  severity: string | null
  enabled: boolean
}

export type NotificationRouteUpdate = {
  alert_code?: string | null
  severity?: string | null
  enabled?: boolean
}

export function createNotificationRoute(
  accessToken: string,
  workspaceId: string,
  payload: NotificationRouteCreate,
) {
  return apiJson<NotificationRoute>(
    '/api/v1/notifications/routes',
    {
      method: 'POST',
      headers: {
        ...workspaceHeaders(
          accessToken,
          workspaceId,
        ),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export function updateNotificationRoute(
  accessToken: string,
  workspaceId: string,
  routeId: string,
  payload: NotificationRouteUpdate,
) {
  return apiJson<NotificationRoute>(
    `/api/v1/notifications/routes/${routeId}`,
    {
      method: 'PATCH',
      headers: {
        ...workspaceHeaders(
          accessToken,
          workspaceId,
        ),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export function deleteNotificationRoute(
  accessToken: string,
  workspaceId: string,
  routeId: string,
) {
  return apiJson<void>(
    `/api/v1/notifications/routes/${routeId}`,
    {
      method: 'DELETE',
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}
