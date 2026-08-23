import {
  useState,
  type FormEvent,
} from 'react'

import {
  Check,
  Clock3,
  ShieldCheck,
  TriangleAlert,
  X,
} from 'lucide-react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  approveActionPlan,
  createActionPlan,
  getActionPlans,
  rejectActionPlan,
  type ActionPlan,
} from '../api/actions'
import {
  getAgents,
} from '../api/agents'
import { ApiError } from '../api/http'
import { useAuth } from '../auth/useAuth'

function formatDate(
  value: string | null,
) {
  if (!value) {
    return '—'
  }

  return new Date(
    value,
  ).toLocaleString()
}

function isSuccessful(
  status: string,
) {
  return status === 'succeeded'
    || status === 'verified'
}

function isActive(
  status: string,
) {
  return status === 'queued'
    || status === 'executing'
    || status === 'verifying'
}

function isFailed(
  status: string,
) {
  return status === 'failed'
    || status === 'rejected'
}

function statusClass(
  status: string,
) {
  return isSuccessful(status)
    ? 'status-badge status-badge--ok'
    : 'status-badge'
}

type DockerContainerOption = {
  name: string
  state: string
}

function dockerContainers(
  value:
    | Array<Record<string, unknown>>
    | undefined,
): DockerContainerOption[] {
  if (!value) {
    return []
  }

  return value.flatMap((item) => {
    const name =
      typeof item.name === 'string'
        ? item.name
        : null

    if (!name) {
      return []
    }

    return [{
      name,
      state:
        typeof item.state === 'string'
          ? item.state
          : 'unknown',
    }]
  })
}

function JsonBlock({
  label,
  value,
}: {
  label: string
  value: Record<string, unknown> | null
}) {
  if (!value) {
    return null
  }

  return (
    <div className="action-parameters">
      <span>{label}</span>
      <code>
        {JSON.stringify(
          value,
          null,
          2,
        )}
      </code>
    </div>
  )
}

function ActionCard({
  plan,
  accessToken,
  workspaceId,
}: {
  plan: ActionPlan
  accessToken: string
  workspaceId: string
}) {
  const queryClient =
    useQueryClient()

  const approve = useMutation({
    mutationFn: () =>
      approveActionPlan(
        accessToken,
        workspaceId,
        plan.id,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['action-plans'],
      })

      void queryClient.invalidateQueries({
        queryKey: ['agents'],
      })
    },
  })

  const reject = useMutation({
    mutationFn: () =>
      rejectActionPlan(
        accessToken,
        workspaceId,
        plan.id,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['action-plans'],
      })
    },
  })

  const pending =
    plan.status === 'pending_approval'

  const busy =
    approve.isPending
    || reject.isPending

  return (
    <article className="action-card">
      <header className="action-card__header">
        <div>
          <div className="agent-title">
            <ShieldCheck size={19} />
            <strong>
              {plan.capability}
            </strong>
          </div>

          <small>
            {plan.id}
          </small>
        </div>

        <span
          className={
            statusClass(plan.status)
          }
        >
          {plan.status}
        </span>
      </header>

      <div className="action-meta">
        <div>
          <span>Risk</span>
          <strong>
            {plan.risk_level}
          </strong>
        </div>

        <div>
          <span>Approval</span>
          <strong>
            {plan.requires_approval
              ? 'Required'
              : 'Not required'}
          </strong>
        </div>

        <div>
          <span>Source</span>
          <strong>
            {plan.source}
          </strong>
        </div>

        <div>
          <span>Verification</span>
          <strong>
            {plan.verification_status ?? '—'}
          </strong>
        </div>
      </div>

      <div className="ops-details">
        <div>
          <span>Resource</span>
          <code>
            {plan.resource_id}
          </code>
        </div>

        <div>
          <span>Created</span>
          <strong>
            {formatDate(plan.created_at)}
          </strong>
        </div>

        <div>
          <span>Approved</span>
          <strong>
            {formatDate(plan.approved_at)}
          </strong>
        </div>

        <div>
          <span>Completed</span>
          <strong>
            {formatDate(plan.completed_at)}
          </strong>
        </div>

        <div>
          <span>Verification started</span>
          <strong>
            {formatDate(
              plan.verification_started_at,
            )}
          </strong>
        </div>

        <div>
          <span>Verified</span>
          <strong>
            {formatDate(plan.verified_at)}
          </strong>
        </div>
      </div>

      <JsonBlock
        label="Parameters"
        value={plan.parameters}
      />

      {plan.rationale && (
        <p className="action-rationale">
          {plan.rationale}
        </p>
      )}

      <JsonBlock
        label="Execution result"
        value={plan.result}
      />

      <JsonBlock
        label="Verification result"
        value={plan.verification_result}
      />

      {pending && (
        <div className="action-controls">
          <button
            type="button"
            className="danger-button"
            disabled={busy}
            onClick={() => {
              const confirmed =
                window.confirm(
                  'Reject action '
                  + plan.capability
                  + '? It will not be queued '
                  + 'for execution.',
                )

              if (confirmed) {
                reject.mutate()
              }
            }}
          >
            <X size={16} />
            {reject.isPending
              ? 'Rejecting…'
              : 'Reject'}
          </button>

          <button
            type="button"
            className="primary-button"
            disabled={busy}
            onClick={() => {
              const confirmed =
                window.confirm(
                  'Approve and queue '
                  + plan.capability
                  + '? This authorizes the '
                  + 'infrastructure mutation '
                  + 'described by this plan.',
                )

              if (confirmed) {
                approve.mutate()
              }
            }}
          >
            <Check size={16} />
            {approve.isPending
              ? 'Approving…'
              : 'Approve & queue'}
          </button>
        </div>
      )}

      {(approve.isError
        || reject.isError)
        && (
          <div className="auth-error">
            Action update failed.
          </div>
        )}
    </article>
  )
}

export function Actions() {
  const auth = useAuth()
  const queryClient = useQueryClient()

  const token =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

  const [
    resourceId,
    setResourceId,
  ] = useState('')

  const [
    container,
    setContainer,
  ] = useState('')

  const [
    rationale,
    setRationale,
  ] = useState('')

  const [
    createError,
    setCreateError,
  ] = useState<string | null>(null)

  const [
    createdPlan,
    setCreatedPlan,
  ] = useState<ActionPlan | null>(null)

  const agents = useQuery({
    queryKey: [
      'agents',
      workspaceId,
    ],
    queryFn: () =>
      getAgents(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  const eligibleAgents =
    (agents.data ?? []).filter(
      (agent) =>
        agent.capabilities.includes(
          'docker.container.restart',
        )
        && agent.metrics?.docker
          ?.available !== false
        && dockerContainers(
          agent.metrics?.docker?.containers,
        ).length > 0,
    )

  const selectedAgent =
    eligibleAgents.find(
      (agent) =>
        agent.resource_id === resourceId,
    )

  const containers =
    dockerContainers(
      selectedAgent?.metrics
        ?.docker?.containers,
    )

  const create = useMutation({
    mutationFn: () =>
      createActionPlan(
        token!,
        workspaceId!,
        {
          resource_id: resourceId,
          capability:
            'docker.container.restart',
          parameters: {
            container,
          },
          rationale:
            rationale.trim() || null,
        },
      ),
    onMutate: () => {
      setCreateError(null)
      setCreatedPlan(null)
    },
    onSuccess: (plan) => {
      setCreatedPlan(plan)
      setContainer('')
      setRationale('')

      void queryClient.invalidateQueries({
        queryKey: [
          'action-plans',
          workspaceId,
        ],
      })
    },
    onError: (error) => {
      setCreateError(
        error instanceof ApiError
          ? error.detail
          : 'action_plan_create_failed',
      )
    },
  })

  function submitActionPlan(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (
      !token
      || !workspaceId
      || !resourceId
      || !container
    ) {
      return
    }

    create.mutate()
  }

  const plans = useQuery({
    queryKey: [
      'action-plans',
      workspaceId,
    ],
    queryFn: () =>
      getActionPlans(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 5_000,
  })

  const data =
    plans.data ?? []

  const pendingApproval =
    data.filter(
      (plan) =>
        plan.status === 'pending_approval',
    ).length

  const active =
    data.filter(
      (plan) =>
        isActive(plan.status),
    ).length

  const successful =
    data.filter(
      (plan) =>
        isSuccessful(plan.status),
    ).length

  const failed =
    data.filter(
      (plan) =>
        isFailed(plan.status),
    ).length

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Policy-controlled execution
          </p>
          <h1>Actions</h1>
          <p>
            Review, approve, execute and verify
            infrastructure mutations through
            existing policy-controlled plans.
          </p>
        </div>

        <div className="system-pill system-pill--online">
          <Clock3 size={16} />
          LIVE QUEUE
        </div>
      </header>

      <section className="panel ops-panel">
        <div className="ops-title">
          <ShieldCheck size={18} />

          <div>
            <strong>
              Manual action plan
            </strong>

            <small>
              Create a policy-controlled Docker
              restart plan from the latest
              observed agent inventory.
            </small>
          </div>
        </div>

        {agents.isLoading && (
          <div className="placeholder">
            Loading actionable resources…
          </div>
        )}

        {agents.isError && (
          <div className="auth-error">
            Actionable resources are unavailable.
          </div>
        )}

        {agents.isSuccess
          && eligibleAgents.length === 0
          && (
            <div className="placeholder">
              No resource currently exposes the
              docker.container.restart capability
              with observed Docker containers.
            </div>
          )}

        {eligibleAgents.length > 0 && (
          <form
            className="action-form"
            onSubmit={submitActionPlan}
          >
            <label className="field-label">
              Resource
            </label>

            <select
              className="control-select"
              value={resourceId}
              onChange={(event) => {
                setResourceId(
                  event.target.value,
                )
                setContainer('')
                setCreatedPlan(null)
                setCreateError(null)
              }}
              required
            >
              <option value="">
                Select resource
              </option>

              {eligibleAgents.map((agent) => (
                <option
                  key={agent.id}
                  value={agent.resource_id}
                >
                  {agent.hostname}
                  {' · '}
                  {agent.status}
                </option>
              ))}
            </select>

            <label className="field-label">
              Capability
            </label>

            <input
              value="docker.container.restart"
              readOnly
            />

            <label className="field-label">
              Container
            </label>

            <select
              className="control-select"
              value={container}
              onChange={(event) => {
                setContainer(
                  event.target.value,
                )
                setCreatedPlan(null)
                setCreateError(null)
              }}
              disabled={!resourceId}
              required
            >
              <option value="">
                Select container
              </option>

              {containers.map((item) => (
                <option
                  key={item.name}
                  value={item.name}
                >
                  {item.name}
                  {' · '}
                  {item.state}
                </option>
              ))}
            </select>

            <label className="field-label">
              Rationale
            </label>

            <textarea
              value={rationale}
              onChange={(event) =>
                setRationale(
                  event.target.value,
                )
              }
              placeholder="Optional operator rationale..."
              maxLength={2000}
              rows={4}
            />

            <div className="placeholder">
              Creating this plan does not execute
              the restart. The backend creates it
              as pending_approval and the existing
              approval flow remains required.
            </div>

            <button
              className="primary-button"
              type="submit"
              disabled={
                create.isPending
                || !resourceId
                || !container
              }
            >
              <ShieldCheck size={17} />
              {create.isPending
                ? 'Creating plan…'
                : 'Create action plan'}
            </button>
          </form>
        )}

        {createError && (
          <div className="auth-error">
            {createError}
          </div>
        )}

        {createdPlan && (
          <div className="ops-success">
            Action plan {createdPlan.id}
            {' created with status '}
            {createdPlan.status}.
          </div>
        )}
      </section>

      <section className="ops-stat-grid">
        <article className="ops-stat">
          <span>Pending approval</span>
          <strong>
            {pendingApproval}
          </strong>
          <small>
            Requires operator decision
          </small>
        </article>

        <article className="ops-stat">
          <span>Active</span>
          <strong>
            {active}
          </strong>
          <small>
            Queued, executing or verifying
          </small>
        </article>

        <article className="ops-stat">
          <span>Successful</span>
          <strong>
            {successful}
          </strong>
          <small>
            Succeeded or verified
          </small>
        </article>

        <article className="ops-stat">
          <span>Failed / rejected</span>
          <strong>
            {failed}
          </strong>
          <small>
            Failed or denied plans
          </small>
        </article>
      </section>

      {pendingApproval > 0 && (
        <section className="panel ops-panel">
          <div className="ops-title">
            <TriangleAlert size={18} />

            <div>
              <strong>
                Operator approval required
              </strong>

              <small>
                {pendingApproval}
                {' action plan'}
                {pendingApproval === 1
                  ? ''
                  : 's'}
                {' waiting for review'}
              </small>
            </div>
          </div>
        </section>
      )}

      {plans.isLoading && (
        <div className="panel">
          Loading action plans…
        </div>
      )}

      {plans.isError && (
        <div className="auth-error">
          Failed to load action plans.
        </div>
      )}

      {plans.data?.length === 0 && (
        <div className="panel empty-state">
          <ShieldCheck size={28} />

          <strong>
            No action plans
          </strong>

          <span>
            AI and operator proposals will
            appear here.
          </span>
        </div>
      )}

      <section className="action-list">
        {token
          && workspaceId
          && plans.data?.map((plan) => (
            <ActionCard
              key={plan.id}
              plan={plan}
              accessToken={token}
              workspaceId={workspaceId}
            />
          ))}
      </section>
    </>
  )
}
