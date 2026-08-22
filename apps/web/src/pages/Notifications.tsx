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
  getNotificationDeliveryProblemCount,
  getNotificationDeliveryProblems,
  getNotificationDestinations,
  getNotificationRoutes,
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
  const workspaceId = auth.workspace?.id

  const health = useQuery({
    queryKey: [
      'notification-health',
      workspaceId,
    ],
    queryFn: () =>
      getNotificationDeliveryHealth(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 10_000,
  })

  const deliveries = useQuery({
    queryKey: [
      'notification-deliveries',
      workspaceId,
    ],
    queryFn: () =>
      getNotificationDeliveries(
        token!,
        workspaceId!,
        50,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 10_000,
  })

  const problems = useQuery({
    queryKey: [
      'notification-delivery-problems',
      workspaceId,
    ],
    queryFn: () =>
      getNotificationDeliveryProblems(
        token!,
        workspaceId!,
        50,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 10_000,
  })

  const problemCount = useQuery({
    queryKey: [
      'notification-delivery-problem-count',
      workspaceId,
    ],
    queryFn: () =>
      getNotificationDeliveryProblemCount(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 10_000,
  })

  const destinations = useQuery({
    queryKey: [
      'notification-destinations',
      workspaceId,
    ],
    queryFn: () =>
      getNotificationDestinations(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 30_000,
  })

  const routes = useQuery({
    queryKey: [
      'notification-routes',
      workspaceId,
    ],
    queryFn: () =>
      getNotificationRoutes(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 30_000,
  })

  const counts = health.data?.total

  const destinationById = new Map(
    (destinations.data ?? []).map(
      (destination) => [
        destination.id,
        destination,
      ],
    ),
  )

  const enabledDestinations =
    destinations.data?.filter(
      (destination) =>
        destination.enabled,
    ).length ?? 0

  const enabledRoutes =
    routes.data?.filter(
      (route) => route.enabled,
    ).length ?? 0

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
        || deliveries.isError
        || problems.isError
        || problemCount.isError
        || destinations.isError
        || routes.isError) && (
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

        <article className="ops-stat">
          <span>Problems</span>
          <strong>
            {problemCount.data?.total ?? '—'}
          </strong>
          <small>
            {problemCount.data
              ? `${problemCount.data.backup} backup · ${problemCount.data.agent_lifecycle} lifecycle`
              : 'Delivery problem records'}
          </small>
        </article>

        <article className="ops-stat">
          <span>Destinations</span>
          <strong>
            {destinations.data
              ? `${enabledDestinations}/${destinations.data.length}`
              : '—'}
          </strong>
          <small>Enabled / configured</small>
        </article>

        <article className="ops-stat">
          <span>Routes</span>
          <strong>
            {routes.data
              ? `${enabledRoutes}/${routes.data.length}`
              : '—'}
          </strong>
          <small>Enabled / configured</small>
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
          <TriangleAlert size={18} />
          <div>
            <strong>
              Delivery problems
            </strong>
            <small>
              Latest 50 problem records
            </small>
          </div>
        </div>

        {problems.isLoading && (
          <div className="ops-empty">
            Loading delivery problems…
          </div>
        )}

        {problems.data?.items.length
          === 0 && (
          <div className="ops-empty">
            No notification delivery problems.
          </div>
        )}

        <div className="ops-list">
          {problems.data?.items.map(
            (delivery) => {
              const destination =
                delivery.destination_id
                  ? destinationById.get(
                      delivery.destination_id,
                    )
                  : undefined

              return (
                <article
                  className="ops-row"
                  key={delivery.id}
                >
                  <div className="ops-row__main">
                    <div className="ops-row__heading">
                      <TriangleAlert
                        size={16}
                      />

                      <strong>
                        {delivery.source}
                      </strong>

                      <span className="status-badge">
                        {delivery.problem}
                      </span>
                    </div>

                    <small>
                      {destination?.name
                        ?? delivery.destination_id
                        ?? 'no destination'}
                      {' · '}
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
              )
            },
          )}
        </div>

        {problems.data?.has_more && (
          <div className="ops-empty">
            Additional problem records exist
            beyond this page.
          </div>
        )}
      </section>

      <section className="panel ops-panel">
        <div className="ops-title">
          <Bell size={18} />
          <div>
            <strong>
              Delivery configuration
            </strong>
            <small>
              Read-only destinations and routes
            </small>
          </div>
        </div>

        {destinations.isLoading
          || routes.isLoading ? (
          <div className="ops-empty">
            Loading delivery configuration…
          </div>
        ) : null}

        {destinations.data?.length === 0 && (
          <div className="ops-empty">
            No notification destinations.
          </div>
        )}

        <div className="ops-list">
          {destinations.data?.map(
            (destination) => {
              const destinationRoutes =
                (routes.data ?? []).filter(
                  (route) =>
                    route.destination_id
                    === destination.id,
                )

              return (
                <article
                  className="ops-row"
                  key={destination.id}
                >
                  <div className="ops-row__main">
                    <div className="ops-row__heading">
                      <Bell size={16} />

                      <strong>
                        {destination.name}
                      </strong>

                      <span
                        className={statusClass(
                          destination.enabled
                            ? 'healthy'
                            : 'disabled',
                        )}
                      >
                        {destination.enabled
                          ? 'enabled'
                          : 'disabled'}
                      </span>
                    </div>

                    <small>
                      {destination.channel}
                      {' · '}
                      {destinationRoutes.length}
                      {' route(s)'}
                    </small>
                  </div>

                  {destinationRoutes.length > 0 && (
                    <div className="inventory-kinds">
                      {destinationRoutes.map(
                        (route) => (
                          <span key={route.id}>
                            {route.alert_code
                              ?? 'any alert'}
                            {' · '}
                            {route.severity
                              ?? 'any severity'}
                            {' · '}
                            {route.enabled
                              ? 'enabled'
                              : 'disabled'}
                          </span>
                        ),
                      )}
                    </div>
                  )}
                </article>
              )
            },
          )}
        </div>
      </section>

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
