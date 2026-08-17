import {
  Check,
  Clock3,
  ShieldCheck,
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

function ActionCard({
  plan,
  accessToken,
}: {
  plan: ActionPlan
  accessToken: string
}) {
  const queryClient =
    useQueryClient()

  const approve = useMutation({
    mutationFn: () =>
      approveActionPlan(
        accessToken,
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
            {formatDate(plan.created_at)}
          </small>
        </div>

        <span
          className={
            plan.status === 'succeeded'
            || plan.status === 'verified'
              ? 'status-badge status-badge--ok'
              : 'status-badge'
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

        <div>
          <span>Approved</span>
          <strong>
            {formatDate(plan.approved_at)}
          </strong>
        </div>
      </div>

      <div className="action-parameters">
        <span>Parameters</span>
        <code>
          {JSON.stringify(
            plan.parameters,
          )}
        </code>
      </div>

      {plan.rationale && (
        <p className="action-rationale">
          {plan.rationale}
        </p>
      )}

      {pending && (
        <div className="action-controls">
          <button
            type="button"
            className="danger-button"
            disabled={busy}
            onClick={() =>
              reject.mutate()
            }
          >
            <X size={16} />
            Reject
          </button>

          <button
            type="button"
            className="primary-button"
            disabled={busy}
            onClick={() =>
              approve.mutate()
            }
          >
            <Check size={16} />
            Approve & queue
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

  const plans = useQuery({
    queryKey: [
      'action-plans',
      auth.workspace?.id,
    ],
    queryFn: () =>
      getActionPlans(token!),
    enabled: Boolean(
      token && auth.workspace,
    ),
    refetchInterval: 5_000,
  })

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Policy-controlled execution
          </p>
          <h1>Actions</h1>
          <p>
            Review, approve and verify
            infrastructure mutations.
          </p>
        </div>

        <div className="system-pill system-pill--online">
          <Clock3 size={16} />
          LIVE QUEUE
        </div>
      </header>

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
          && plans.data?.map((plan) => (
            <ActionCard
              key={plan.id}
              plan={plan}
              accessToken={token}
            />
          ))}
      </section>
    </>
  )
}
