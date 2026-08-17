import {
  Bell,
  CheckCircle2,
  Clock3,
  Send,
  TriangleAlert,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import {
  getNotificationDeliveries,
  getNotificationDeliveryHealth,
} from '../api/notifications'
import { useAuth } from '../auth/useAuth'

function formatDate(
  value: string | null,
) {
  if (!value) {
    return '—'
  }

  return new Date(value).toLocaleString()
}

function statusClass(
  status: string | undefined,
) {
  return status === 'healthy'
    || status === 'ok'
    || status === 'delivered'
      ? 'status-badge status-badge--ok'
      : 'status-badge'
}

export function Notifications() {
  const auth = useAuth()
  const token = auth.tokens?.access_token

  const health = useQuery({
    queryKey: [
      'notification-health',
      auth.workspace?.id,
    ],
    queryFn: () =>
      getNotificationDeliveryHealth(token!),
    enabled: Boolean(
      token && auth.workspace,
    ),
    refetchInterval: 10_000,
  })

  const deliveries = useQuery({
    queryKey: [
      'notification-deliveries',
      auth.workspace?.id,
    ],
    queryFn: () =>
      getNotificationDeliveries(
        token!,
        50,
      ),
    enabled: Boolean(
      token && auth.workspace,
    ),
    refetchInterval: 10_000,
  })

  const counts = health.data?.total

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Delivery observability
          </p>
          <h1>Notifications</h1>
          <p>
            Delivery health, retries and
            recent notification activity.
          </p>
        </div>

        <div className="system-pill">
          <Bell size={16} />
          DELIVERY
        </div>
      </header>

      {(health.isError
        || deliveries.isError) && (
        <div className="auth-error">
          Failed to load notification
          observability.
        </div>
      )}

      <section className="ops-stat-grid">
        <article className="ops-stat">
          <span>Health</span>
          <strong>
            {health.data?.status ?? '—'}
          </strong>
          <small>
            {health.data?.issues.length
              ? `${health.data.issues.length} issue(s)`
              : 'No reported issues'}
          </small>
        </article>

        <article className="ops-stat">
          <span>Total</span>
          <strong>
            {counts?.total ?? '—'}
          </strong>
          <small>
            Recorded deliveries
          </small>
        </article>

        <article className="ops-stat">
          <span>Delivered</span>
          <strong>
            {counts?.delivered ?? '—'}
          </strong>
          <small>
            Completed successfully
          </small>
        </article>

        <article className="ops-stat">
          <span>Failed</span>
          <strong>
            {counts?.failed ?? '—'}
          </strong>
          <small>
            {counts
              ? `${counts.retryable_failed} retryable`
              : '—'}
          </small>
        </article>
      </section>

      {health.data?.issues
        && health.data.issues.length > 0
        && (
          <section className="panel ops-panel">
            <div className="ops-title">
              <TriangleAlert size={18} />
              <strong>Delivery issues</strong>
            </div>

            <ul className="ops-issues">
              {health.data.issues.map(
                (issue) => (
                  <li key={issue}>
                    {issue}
                  </li>
                ),
              )}
            </ul>
          </section>
        )}

      <section className="panel ops-panel">
        <div className="ops-title">
          <Send size={18} />
          <div>
            <strong>
              Recent deliveries
            </strong>
            <small>
              Latest 50 delivery records
            </small>
          </div>
        </div>

        {deliveries.isLoading && (
          <div className="ops-empty">
            Loading deliveries…
          </div>
        )}

        {deliveries.data?.items.length
          === 0 && (
          <div className="ops-empty">
            No notification deliveries.
          </div>
        )}

        <div className="ops-list">
          {deliveries.data?.items.map(
            (delivery) => (
              <article
                className="ops-row"
                key={delivery.id}
              >
                <div className="ops-row__main">
                  <div className="ops-row__heading">
                    {delivery.status
                      === 'delivered'
                      ? (
                          <CheckCircle2
                            size={16}
                          />
                        )
                      : (
                          <Clock3
                            size={16}
                          />
                        )}

                    <strong>
                      {delivery.source}
                    </strong>

                    <span
                      className={statusClass(
                        delivery.status,
                      )}
                    >
                      {delivery.status}
                    </span>
                  </div>

                  <small>
                    {delivery.channel}
                    {' · '}
                    attempts{' '}
                    {delivery.attempts}/
                    {delivery.max_attempts}
                    {' · '}
                    {formatDate(
                      delivery.created_at,
                    )}
                  </small>
                </div>

                {delivery.last_error && (
                  <code className="ops-error">
                    {delivery.last_error}
                  </code>
                )}
              </article>
            ),
          )}
        </div>
      </section>
    </>
  )
}
