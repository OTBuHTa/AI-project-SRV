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
  getActionPlans,
  rejectActionPlan,
  type ActionPlan,
} from '../api/actions'
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

  const token =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

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
