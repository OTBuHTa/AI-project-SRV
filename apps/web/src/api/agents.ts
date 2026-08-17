import {
  apiJson,
  bearerHeaders,
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

export function getAgents(
  accessToken: string,
) {
  return apiJson<Agent[]>(
    '/api/v1/agents',
    {
      headers: bearerHeaders(accessToken),
    },
  )
}

export function getAgentTelemetry(
  accessToken: string,
  agentId: string,
  limit = 60,
) {
  return apiJson<TelemetryPoint[]>(
    `/api/v1/agents/${agentId}/telemetry?limit=${limit}`,
    {
      headers: bearerHeaders(accessToken),
    },
  )
}

export function getResourceHealth(
  accessToken: string,
  resourceId: string,
) {
  return apiJson<ResourceHealth>(
    `/api/v1/ai/tools/resource-health/${resourceId}`,
    {
      headers: bearerHeaders(accessToken),
    },
  )
}

export function getInventorySummary(
  accessToken: string,
  resourceId: string,
) {
  return apiJson<InventorySummary>(
    `/api/v1/inventory/resources/${resourceId}/summary`,
    {
      headers: bearerHeaders(accessToken),
    },
  )
}
