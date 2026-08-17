import {
  apiJson,
  bearerHeaders,
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
  resourceId: string,
  message: string,
  container?: string,
) {
  return apiJson<ActionProposal>(
    '/api/v1/ai/action-proposals',
    {
      method: 'POST',
      headers: {
        ...bearerHeaders(accessToken),
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

export function getActionPlans(
  accessToken: string,
) {
  return apiJson<ActionPlan[]>(
    '/api/v1/action-plans',
    {
      headers: bearerHeaders(accessToken),
    },
  )
}

export function approveActionPlan(
  accessToken: string,
  planId: string,
) {
  return apiJson<ActionPlan>(
    `/api/v1/action-plans/${planId}/approve`,
    {
      method: 'POST',
      headers: bearerHeaders(accessToken),
    },
  )
}

export function rejectActionPlan(
  accessToken: string,
  planId: string,
) {
  return apiJson<ActionPlan>(
    `/api/v1/action-plans/${planId}/reject`,
    {
      method: 'POST',
      headers: bearerHeaders(accessToken),
    },
  )
}
