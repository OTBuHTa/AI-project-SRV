import {
  apiJson,
  workspaceHeaders,
} from './http'

export type ActionPlan = {
  id: string
  resource_id: string
  capability: string
  parameters: Record<string, unknown>
  rationale: string | null
  risk_level: number
  requires_approval: boolean
  status: string
  approved_by_user_id: string | null
  approved_at: string | null
  completed_at: string | null
  result: Record<string, unknown> | null
  source: string
  verification_status: string | null
  verification_result:
    Record<string, unknown> | null
  verification_started_at: string | null
  verified_at: string | null
  created_at: string
}

export type ActionProposal = {
  action_plan_id: string
  resource_id: string
  capability: string
  parameters: Record<string, unknown>
  rationale: string
  risk_level: number
  requires_approval: boolean
  status: string
  source: string
  created_at: string
}

export function createActionProposal(
  accessToken: string,
  workspaceId: string,
  resourceId: string,
  message: string,
  container?: string,
) {
  return apiJson<ActionProposal>(
    '/api/v1/ai/action-proposals',
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
        resource_id: resourceId,
        message,
        container: container || null,
      }),
    },
  )
}

export type ActionPlanCreate = {
  resource_id: string
  capability: 'docker.container.restart'
  parameters: {
    container: string
  }
  rationale: string | null
}

export function createActionPlan(
  accessToken: string,
  workspaceId: string,
  payload: ActionPlanCreate,
) {
  return apiJson<ActionPlan>(
    '/api/v1/action-plans',
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

export function getActionPlans(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<ActionPlan[]>(
    '/api/v1/action-plans',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function approveActionPlan(
  accessToken: string,
  workspaceId: string,
  planId: string,
) {
  return apiJson<ActionPlan>(
    `/api/v1/action-plans/${planId}/approve`,
    {
      method: 'POST',
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function rejectActionPlan(
  accessToken: string,
  workspaceId: string,
  planId: string,
) {
  return apiJson<ActionPlan>(
    `/api/v1/action-plans/${planId}/reject`,
    {
      method: 'POST',
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}
