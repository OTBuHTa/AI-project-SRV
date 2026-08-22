import {
  apiJson,
  workspaceHeaders,
} from './http'

export type DockerSummary = {
  available?: boolean
  containers_total?: number
  containers_running?: number
  containers_stopped?: number
  containers?: Array<Record<string, unknown>>
}

export type SystemMetrics = {
  cpu_percent?: number
  memory_percent?: number
  disk_percent?: number
  disk_free_bytes?: number
  uptime_seconds?: number
  load_1m?: number | null
  docker?: DockerSummary | null
}

export type Agent = {
  id: string
  resource_id: string
  hostname: string
  agent_type: string
  version: string
  status: string
  last_seen_at: string | null
  capabilities: string[]
  metrics: SystemMetrics | null
}

export type TelemetryPoint = {
  timestamp: string
  cpu_percent: number
  memory_percent: number
  disk_percent: number
  disk_free_bytes: number
  uptime_seconds: number
  load_1m: number | null
  docker: DockerSummary | null
}

export type ResourceHealth = {
  resource_id: string
  hostname: string
  status: string
  health_score: number
  severity: string
  findings: string[]
  metrics: SystemMetrics | null
  docker: DockerSummary | null
  last_seen_at: string | null
}

export type InventorySummary = {
  resource_id: string
  total_items: number
  kinds: Record<string, number>
  lifecycle: Record<string, number>
}

export type InventoryLifecycleStatus =
  | 'observed'
  | 'stale'
  | 'absent'

export type InventoryItem = {
  id: string
  workspace_id: string
  resource_id: string
  kind: string
  external_id: string
  name: string
  status: string
  attributes: Record<string, unknown>
  observed_at: string
  last_seen_at: string | null
  lifecycle_status: InventoryLifecycleStatus
  created_at: string
  updated_at: string
}

export type InventoryFilters = {
  kind?: string
  lifecycleStatus?: InventoryLifecycleStatus
}

export type AgentTokenRotateResponse = {
  agent_token: string
  agent_token_expires_at: string
  token_rotated_at: string
}

export function rotateAgentToken(
  accessToken: string,
  workspaceId: string,
  agentId: string,
) {
  return apiJson<AgentTokenRotateResponse>(
    `/api/v1/agents/${agentId}/token/rotate`,
    {
      method: 'POST',
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getAgents(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<Agent[]>(
    '/api/v1/agents',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getAgentTelemetry(
  accessToken: string,
  workspaceId: string,
  agentId: string,
  limit = 60,
) {
  return apiJson<TelemetryPoint[]>(
    `/api/v1/agents/${agentId}/telemetry?limit=${limit}`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getResourceHealth(
  accessToken: string,
  workspaceId: string,
  resourceId: string,
) {
  return apiJson<ResourceHealth>(
    `/api/v1/ai/tools/resource-health/${resourceId}`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getInventorySummary(
  accessToken: string,
  workspaceId: string,
  resourceId: string,
) {
  return apiJson<InventorySummary>(
    `/api/v1/inventory/resources/${resourceId}/summary`,
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getResourceInventory(
  accessToken: string,
  workspaceId: string,
  resourceId: string,
  filters: InventoryFilters = {},
) {
  const params = new URLSearchParams()

  if (filters.kind) {
    params.set('kind', filters.kind)
  }

  if (filters.lifecycleStatus) {
    params.set(
      'lifecycle_status',
      filters.lifecycleStatus,
    )
  }

  const query = params.toString()

  return apiJson<InventoryItem[]>(
    `/api/v1/inventory/resources/${resourceId}/items`
      + (query ? `?${query}` : ''),
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}
