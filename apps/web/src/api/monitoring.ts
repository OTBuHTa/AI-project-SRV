import {
  apiJson,
  workspaceHeaders,
} from './http'

export type AgentTokenLifecycleDiagnostics = {
  status: string
  issues: string[]
  workspace_id: string
  agents_total: number
  pending_rotations: number
  expired_pending_rotations: number
  incomplete_pending_rotations: number
  revoked_with_pending_rotation: number
  oldest_pending_prepared_at: string | null
  prepare_ttl_seconds: number
  observed_at: string
}

export type AgentLifecycleAlertEvent = {
  id: string
  workspace_id: string
  code: string
  severity: string
  message: string
  active: boolean
  first_seen_at: string
  last_seen_at: string
  resolved_at: string | null
}

export function getAgentTokenLifecycleDiagnostics(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<AgentTokenLifecycleDiagnostics>(
    '/api/v1/monitoring/agent-token-lifecycle',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getActiveAgentLifecycleAlerts(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<AgentLifecycleAlertEvent[]>(
    '/api/v1/monitoring/agent-lifecycle-alert-events/active',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getAgentLifecycleAlerts(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<AgentLifecycleAlertEvent[]>(
    '/api/v1/monitoring/agent-lifecycle-alert-events',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}
