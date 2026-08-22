import {
  Bell,
  CheckCircle2,
  Clock3,
  Filter,
  Send,
  TriangleAlert,
} from 'lucide-react'
import {
  useQuery,
  useMutation,
} from '@tanstack/react-query'
import { useState } from 'react'

import {
  getNotificationDeliveries,
  getNotificationDeliveryCount,
  getNotificationDeliveryHealth,
  getNotificationDeliveryProblemCount,
  getNotificationDeliveryProblems,
  getNotificationDestinations,
  getNotificationRoutes,
  type NotificationDeliveryFilters,
  createNotificationDestination,
  deleteNotificationDestination,
  updateNotificationDestination,
  createNotificationRoute,
  deleteNotificationRoute,
  updateNotificationRoute,
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


type DestinationManagerItem = {
  id: string
  name: string
  channel: string
  endpoint: string
  enabled: boolean
}

type DestinationManagerRoute = {
  destination_id: string
}

function NotificationDestinationManager({
  accessToken,
  workspaceId,
  destinations,
  routes,
  onRefresh,
}: {
  accessToken: string
  workspaceId: string
  destinations: DestinationManagerItem[]
  routes: DestinationManagerRoute[]
  onRefresh: () => Promise<unknown>
}) {
  const [createName, setCreateName] =
    useState('')
  const [createEndpoint, setCreateEndpoint] =
    useState('')
  const [createEnabled, setCreateEnabled] =
    useState(true)

  const [editingId, setEditingId] =
    useState<string | null>(null)
  const [editName, setEditName] =
    useState('')
  const [editEndpoint, setEditEndpoint] =
    useState('')

  const createDestination = useMutation({
    mutationFn: () =>
      createNotificationDestination(
        accessToken,
        workspaceId,
        {
          name: createName.trim(),
          channel: 'webhook',
          endpoint: createEndpoint.trim(),
          enabled: createEnabled,
        },
      ),
    onSuccess: async () => {
      setCreateName('')
      setCreateEndpoint('')
      setCreateEnabled(true)
      await onRefresh()
    },
  })

  const saveDestination = useMutation({
    mutationFn: ({
      destinationId,
      name,
      endpoint,
    }: {
      destinationId: string
      name: string
      endpoint: string
    }) =>
      updateNotificationDestination(
        accessToken,
        workspaceId,
        destinationId,
        {
          name: name.trim(),
          endpoint: endpoint.trim(),
        },
      ),
    onSuccess: async () => {
      setEditingId(null)
      setEditName('')
      setEditEndpoint('')
      await onRefresh()
    },
  })

  const toggleDestination = useMutation({
    mutationFn: ({
      destinationId,
      enabled,
    }: {
      destinationId: string
      enabled: boolean
    }) =>
      updateNotificationDestination(
        accessToken,
        workspaceId,
        destinationId,
        {
          enabled,
        },
      ),
    onSuccess: async () => {
      await onRefresh()
    },
  })

  const removeDestination = useMutation({
    mutationFn: (destinationId: string) =>
      deleteNotificationDestination(
        accessToken,
        workspaceId,
        destinationId,
      ),
    onSuccess: async () => {
      setEditingId(null)
      await onRefresh()
    },
  })

  const startEdit = (
    destination: DestinationManagerItem,
  ) => {
    setEditingId(destination.id)
    setEditName(destination.name)
    setEditEndpoint(destination.endpoint)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditName('')
    setEditEndpoint('')
  }

  const mutationError =
    createDestination.isError
    || saveDestination.isError
    || toggleDestination.isError
    || removeDestination.isError

  return (
    <section className="panel ops-panel">
      <div className="ops-title">
        <div>
          <strong>
            Notification destinations
          </strong>
          <small>
            Manage webhook delivery endpoints.
          </small>
        </div>
      </div>

      {mutationError && (
        <div className="auth-error">
          Notification destination operation failed.
        </div>
      )}

      <div className="notification-filter-grid">
        <label className="field-label">
          Name
          <input
            className="control-input"
            value={createName}
            maxLength={128}
            placeholder="operations"
            onChange={(event) =>
              setCreateName(event.target.value)
            }
          />
        </label>

        <label className="field-label">
          Channel
          <input
            className="control-input"
            value="webhook"
            readOnly
            disabled
          />
        </label>

        <label className="field-label">
          Endpoint
          <input
            className="control-input"
            value={createEndpoint}
            placeholder="https://example.com/alerts"
            onChange={(event) =>
              setCreateEndpoint(
                event.target.value,
              )
            }
          />
        </label>

        <label className="field-label">
          Enabled
          <input
            type="checkbox"
            checked={createEnabled}
            onChange={(event) =>
              setCreateEnabled(
                event.target.checked,
              )
            }
          />
        </label>
      </div>

      <div className="notification-filter-actions">
        <button
          type="button"
          className="sidebar-action"
          disabled={
            createDestination.isPending
            || createName.trim().length === 0
            || createEndpoint.trim().length === 0
          }
          onClick={() =>
            createDestination.mutate()
          }
        >
          {createDestination.isPending
            ? 'Creating…'
            : 'Create destination'}
        </button>
      </div>

      {destinations.length === 0 && (
        <div className="ops-empty">
          No notification destinations configured.
        </div>
      )}

      <div className="ops-list">
        {destinations.map((destination) => {
          const routeCount = routes.filter(
            (route) =>
              route.destination_id
              === destination.id,
          ).length

          const editing =
            editingId === destination.id

          const saving =
            saveDestination.isPending
            && saveDestination.variables
              ?.destinationId
              === destination.id

          const toggling =
            toggleDestination.isPending
            && toggleDestination.variables
              ?.destinationId
              === destination.id

          const deleting =
            removeDestination.isPending
            && removeDestination.variables
              === destination.id

          const busy =
            saving || toggling || deleting

          return (
            <article
              className="ops-row"
              key={destination.id}
            >
              <div className="ops-row__main">
                <div className="ops-row__heading">
                  <strong>
                    {destination.name}
                  </strong>

                  <span
                    className={
                      destination.enabled
                        ? (
                            'status-badge '
                            + 'status-badge--ok'
                          )
                        : 'status-badge'
                    }
                  >
                    {destination.enabled
                      ? 'enabled'
                      : 'disabled'}
                  </span>

                  <span className="status-badge">
                    {destination.channel}
                  </span>
                </div>

                <small>
                  {routeCount} route
                  {routeCount === 1 ? '' : 's'}
                </small>
              </div>

              {editing ? (
                <>
                  <div className="notification-filter-grid">
                    <label className="field-label">
                      Name
                      <input
                        className="control-input"
                        value={editName}
                        maxLength={128}
                        onChange={(event) =>
                          setEditName(
                            event.target.value,
                          )
                        }
                      />
                    </label>

                    <label className="field-label">
                      Endpoint
                      <input
                        className="control-input"
                        value={editEndpoint}
                        onChange={(event) =>
                          setEditEndpoint(
                            event.target.value,
                          )
                        }
                      />
                    </label>
                  </div>

                  <div className="notification-filter-actions">
                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={
                        busy
                        || editName.trim().length
                          === 0
                        || editEndpoint.trim().length
                          === 0
                      }
                      onClick={() =>
                        saveDestination.mutate({
                          destinationId:
                            destination.id,
                          name: editName,
                          endpoint:
                            editEndpoint,
                        })
                      }
                    >
                      {saving
                        ? 'Saving…'
                        : 'Save'}
                    </button>

                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={busy}
                      onClick={cancelEdit}
                    >
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <span>
                    {destination.endpoint}
                  </span>

                  <div className="notification-filter-actions">
                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={busy}
                      onClick={() =>
                        startEdit(destination)
                      }
                    >
                      Edit
                    </button>

                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={busy}
                      onClick={() =>
                        toggleDestination.mutate({
                          destinationId:
                            destination.id,
                          enabled:
                            !destination.enabled,
                        })
                      }
                    >
                      {toggling
                        ? 'Updating…'
                        : (
                            destination.enabled
                              ? 'Disable'
                              : 'Enable'
                          )}
                    </button>

                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={busy}
                      onClick={() => {
                        const suffix =
                          routeCount > 0
                            ? (
                                ` ${routeCount} associated `
                                + `route${
                                  routeCount === 1
                                    ? ''
                                    : 's'
                                } will also be deleted.`
                              )
                            : ''

                        if (
                          window.confirm(
                            `Delete ${destination.name}?`
                            + suffix,
                          )
                        ) {
                          removeDestination.mutate(
                            destination.id,
                          )
                        }
                      }}
                    >
                      {deleting
                        ? 'Deleting…'
                        : 'Delete'}
                    </button>
                  </div>
                </>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}


type RouteManagerItem = {
  id: string
  destination_id: string
  alert_code: string | null
  severity: string | null
  enabled: boolean
}

function NotificationRouteManager({
  accessToken,
  workspaceId,
  destinations,
  routes,
  onRefresh,
}: {
  accessToken: string
  workspaceId: string
  destinations: DestinationManagerItem[]
  routes: RouteManagerItem[]
  onRefresh: () => Promise<unknown>
}) {
  const [createDestinationId, setCreateDestinationId] =
    useState('')
  const [createAlertCode, setCreateAlertCode] =
    useState('')
  const [createSeverity, setCreateSeverity] =
    useState('')
  const [createEnabled, setCreateEnabled] =
    useState(true)

  const [editingId, setEditingId] =
    useState<string | null>(null)
  const [editAlertCode, setEditAlertCode] =
    useState('')
  const [editSeverity, setEditSeverity] =
    useState('')

  const createRoute = useMutation({
    mutationFn: () =>
      createNotificationRoute(
        accessToken,
        workspaceId,
        {
          destination_id: createDestinationId,
          alert_code:
            createAlertCode.trim() || null,
          severity:
            createSeverity.trim() || null,
          enabled: createEnabled,
        },
      ),
    onSuccess: async () => {
      setCreateDestinationId('')
      setCreateAlertCode('')
      setCreateSeverity('')
      setCreateEnabled(true)
      await onRefresh()
    },
  })

  const saveRoute = useMutation({
    mutationFn: ({
      routeId,
      alertCode,
      severity,
    }: {
      routeId: string
      alertCode: string
      severity: string
    }) =>
      updateNotificationRoute(
        accessToken,
        workspaceId,
        routeId,
        {
          alert_code:
            alertCode.trim() || null,
          severity:
            severity.trim() || null,
        },
      ),
    onSuccess: async () => {
      setEditingId(null)
      setEditAlertCode('')
      setEditSeverity('')
      await onRefresh()
    },
  })

  const toggleRoute = useMutation({
    mutationFn: ({
      routeId,
      enabled,
    }: {
      routeId: string
      enabled: boolean
    }) =>
      updateNotificationRoute(
        accessToken,
        workspaceId,
        routeId,
        {
          enabled,
        },
      ),
    onSuccess: async () => {
      await onRefresh()
    },
  })

  const removeRoute = useMutation({
    mutationFn: (routeId: string) =>
      deleteNotificationRoute(
        accessToken,
        workspaceId,
        routeId,
      ),
    onSuccess: async () => {
      setEditingId(null)
      await onRefresh()
    },
  })

  const startEdit = (
    route: RouteManagerItem,
  ) => {
    setEditingId(route.id)
    setEditAlertCode(
      route.alert_code ?? '',
    )
    setEditSeverity(
      route.severity ?? '',
    )
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditAlertCode('')
    setEditSeverity('')
  }

  const destinationName = (
    destinationId: string,
  ) =>
    destinations.find(
      (destination) =>
        destination.id === destinationId,
    )?.name ?? destinationId

  const mutationError =
    createRoute.isError
    || saveRoute.isError
    || toggleRoute.isError
    || removeRoute.isError

  return (
    <section className="panel ops-panel">
      <div className="ops-title">
        <div>
          <strong>
            Notification routes
          </strong>
          <small>
            Manage destination routing rules.
          </small>
        </div>
      </div>

      {mutationError && (
        <div className="auth-error">
          Notification route operation failed.
        </div>
      )}

      <div className="notification-filter-grid">
        <label className="field-label">
          Destination
          <select
            className="control-select"
            value={createDestinationId}
            onChange={(event) =>
              setCreateDestinationId(
                event.target.value,
              )
            }
          >
            <option value="">
              Select destination
            </option>

            {destinations.map(
              (destination) => (
                <option
                  key={destination.id}
                  value={destination.id}
                >
                  {destination.name}
                </option>
              ),
            )}
          </select>
        </label>

        <label className="field-label">
          Alert code
          <input
            className="control-input"
            value={createAlertCode}
            maxLength={64}
            placeholder="any alert"
            onChange={(event) =>
              setCreateAlertCode(
                event.target.value,
              )
            }
          />
        </label>

        <label className="field-label">
          Severity
          <input
            className="control-input"
            value={createSeverity}
            maxLength={32}
            placeholder="any severity"
            onChange={(event) =>
              setCreateSeverity(
                event.target.value,
              )
            }
          />
        </label>

        <label className="field-label">
          Enabled
          <input
            type="checkbox"
            checked={createEnabled}
            onChange={(event) =>
              setCreateEnabled(
                event.target.checked,
              )
            }
          />
        </label>
      </div>

      <div className="notification-filter-actions">
        <button
          type="button"
          className="sidebar-action"
          disabled={
            createRoute.isPending
            || createDestinationId.length === 0
          }
          onClick={() =>
            createRoute.mutate()
          }
        >
          {createRoute.isPending
            ? 'Creating…'
            : 'Create route'}
        </button>
      </div>

      {destinations.length === 0 && (
        <div className="ops-empty">
          Create a notification destination
          before adding routes.
        </div>
      )}

      {routes.length === 0 && (
        <div className="ops-empty">
          No notification routes configured.
        </div>
      )}

      <div className="ops-list">
        {routes.map((route) => {
          const editing =
            editingId === route.id

          const saving =
            saveRoute.isPending
            && saveRoute.variables
              ?.routeId === route.id

          const toggling =
            toggleRoute.isPending
            && toggleRoute.variables
              ?.routeId === route.id

          const deleting =
            removeRoute.isPending
            && removeRoute.variables
              === route.id

          const busy =
            saving || toggling || deleting

          return (
            <article
              className="ops-row"
              key={route.id}
            >
              <div className="ops-row__main">
                <div className="ops-row__heading">
                  <strong>
                    {destinationName(
                      route.destination_id,
                    )}
                  </strong>

                  <span
                    className={
                      route.enabled
                        ? (
                            'status-badge '
                            + 'status-badge--ok'
                          )
                        : 'status-badge'
                    }
                  >
                    {route.enabled
                      ? 'enabled'
                      : 'disabled'}
                  </span>
                </div>

                <small>
                  {route.alert_code
                    ?? 'any alert'}
                  {' · '}
                  {route.severity
                    ?? 'any severity'}
                </small>
              </div>

              {editing ? (
                <>
                  <div className="notification-filter-grid">
                    <label className="field-label">
                      Alert code
                      <input
                        className="control-input"
                        value={editAlertCode}
                        maxLength={64}
                        placeholder="any alert"
                        onChange={(event) =>
                          setEditAlertCode(
                            event.target.value,
                          )
                        }
                      />
                    </label>

                    <label className="field-label">
                      Severity
                      <input
                        className="control-input"
                        value={editSeverity}
                        maxLength={32}
                        placeholder="any severity"
                        onChange={(event) =>
                          setEditSeverity(
                            event.target.value,
                          )
                        }
                      />
                    </label>
                  </div>

                  <div className="notification-filter-actions">
                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={busy}
                      onClick={() =>
                        saveRoute.mutate({
                          routeId: route.id,
                          alertCode:
                            editAlertCode,
                          severity:
                            editSeverity,
                        })
                      }
                    >
                      {saving
                        ? 'Saving…'
                        : 'Save'}
                    </button>

                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={busy}
                      onClick={cancelEdit}
                    >
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <div className="notification-filter-actions">
                  <button
                    type="button"
                    className="sidebar-action"
                    disabled={busy}
                    onClick={() =>
                      startEdit(route)
                    }
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="sidebar-action"
                    disabled={busy}
                    onClick={() =>
                      toggleRoute.mutate({
                        routeId: route.id,
                        enabled: !route.enabled,
                      })
                    }
                  >
                    {toggling
                      ? 'Updating…'
                      : (
                          route.enabled
                            ? 'Disable'
                            : 'Enable'
                        )}
                  </button>

                  <button
                    type="button"
                    className="sidebar-action"
                    disabled={busy}
                    onClick={() => {
                      if (
                        window.confirm(
                          'Delete this notification route?',
                        )
                      ) {
                        removeRoute.mutate(
                          route.id,
                        )
                      }
                    }}
                  >
                    {deleting
                      ? 'Deleting…'
                      : 'Delete'}
                  </button>
                </div>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}

export function Notifications() {
  const auth = useAuth()
  const token = auth.tokens?.access_token
  const workspaceId = auth.workspace?.id

  const [
    draftFilters,
    setDraftFilters,
  ] = useState<NotificationDeliveryFilters>({})

  const [
    appliedFilters,
    setAppliedFilters,
  ] = useState<NotificationDeliveryFilters>({})

  const [
    deliveryCursorStack,
    setDeliveryCursorStack,
  ] = useState<string[]>([])

  const [
    problemCursorStack,
    setProblemCursorStack,
  ] = useState<string[]>([])

  const deliveryCursor =
    deliveryCursorStack[
      deliveryCursorStack.length - 1
    ]

  const problemCursor =
    problemCursorStack[
      problemCursorStack.length - 1
    ]

  const applyFilters = () => {
    setAppliedFilters({
      ...draftFilters,
      cursor: undefined,
    })
    setDeliveryCursorStack([])
    setProblemCursorStack([])
  }

  const resetFilters = () => {
    setDraftFilters({})
    setAppliedFilters({})
    setDeliveryCursorStack([])
    setProblemCursorStack([])
  }

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
      appliedFilters,
      deliveryCursor,
    ],
    queryFn: () =>
      getNotificationDeliveries(
        token!,
        workspaceId!,
        {
          ...appliedFilters,
          cursor: deliveryCursor,
        },
        50,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval:
      deliveryCursor
        ? false
        : 10_000,
  })

  const deliveryCount = useQuery({
    queryKey: [
      'notification-delivery-count',
      workspaceId,
      appliedFilters,
    ],
    queryFn: () =>
      getNotificationDeliveryCount(
        token!,
        workspaceId!,
        appliedFilters,
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
      appliedFilters,
      problemCursor,
    ],
    queryFn: () =>
      getNotificationDeliveryProblems(
        token!,
        workspaceId!,
        {
          ...appliedFilters,
          cursor: problemCursor,
        },
        50,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval:
      problemCursor
        ? false
        : 10_000,
  })

  const problemCount = useQuery({
    queryKey: [
      'notification-delivery-problem-count',
      workspaceId,
      appliedFilters,
    ],
    queryFn: () =>
      getNotificationDeliveryProblemCount(
        token!,
        workspaceId!,
        appliedFilters,
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

  const channelOptions = Array.from(
    new Set(
      (destinations.data ?? [])
        .map(
          (destination) =>
            destination.channel,
        )
        .filter(Boolean),
    ),
  ).sort()

  const activeFilterCount =
    Object.values(appliedFilters)
      .filter(Boolean)
      .length

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

      {token && workspaceId && (
        <NotificationDestinationManager
          accessToken={token}
          workspaceId={workspaceId}
          destinations={
            destinations.data ?? []
          }
          routes={routes.data ?? []}
          onRefresh={async () => {
            await Promise.all([
              destinations.refetch(),
              routes.refetch(),
            ])
          }}
        />
      )}



      {token && workspaceId && (
        <NotificationRouteManager
          accessToken={token}
          workspaceId={workspaceId}
          destinations={
            destinations.data ?? []
          }
          routes={routes.data ?? []}
          onRefresh={async () => {
            await routes.refetch()
          }}
        />
      )}

      {(health.isError
        || deliveries.isError
        || deliveryCount.isError
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
          <span>Matching deliveries</span>
          <strong>
            {deliveryCount.data?.total ?? '—'}
          </strong>
          <small>
            {deliveryCount.data
              ? `${deliveryCount.data.backup} backup · ${deliveryCount.data.agent_lifecycle} lifecycle`
              : 'Filtered delivery count'}
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

      <section className="panel ops-panel">
        <div className="ops-title">
          <Filter size={18} />
          <div>
            <strong>
              Delivery explorer
            </strong>
            <small>
              {activeFilterCount > 0
                ? `${activeFilterCount} active filter(s)`
                : 'All notification deliveries'}
            </small>
          </div>
        </div>

        <div className="notification-filter-grid">
          <label className="field-label">
            Source
            <select
              className="control-select"
              value={draftFilters.source ?? ''}
              onChange={(event) => {
                const value = event.target.value

                setDraftFilters(
                  (current) => ({
                    ...current,
                    source:
                      value === 'backup'
                      || value === 'agent_lifecycle'
                        ? value
                        : undefined,
                  }),
                )
              }}
            >
              <option value="">All sources</option>
              <option value="backup">
                backup
              </option>
              <option value="agent_lifecycle">
                agent_lifecycle
              </option>
            </select>
          </label>

          <label className="field-label">
            Status
            <select
              className="control-select"
              value={draftFilters.status ?? ''}
              onChange={(event) => {
                const value = event.target.value

                setDraftFilters(
                  (current) => ({
                    ...current,
                    status:
                      value === 'pending'
                      || value === 'sending'
                      || value === 'delivered'
                      || value === 'failed'
                      || value === 'canceled'
                        ? value
                        : undefined,
                  }),
                )
              }}
            >
              <option value="">All statuses</option>
              <option value="pending">
                pending
              </option>
              <option value="sending">
                sending
              </option>
              <option value="delivered">
                delivered
              </option>
              <option value="failed">
                failed
              </option>
              <option value="canceled">
                canceled
              </option>
            </select>
          </label>

          <label className="field-label">
            Problem
            <select
              className="control-select"
              value={draftFilters.problem ?? ''}
              onChange={(event) => {
                const value = event.target.value

                setDraftFilters(
                  (current) => ({
                    ...current,
                    problem:
                      value === 'retryable_failed'
                      || value === 'exhausted_failed'
                      || value === 'stale_sending'
                        ? value
                        : undefined,
                  }),
                )
              }}
            >
              <option value="">All problems</option>
              <option value="retryable_failed">
                retryable_failed
              </option>
              <option value="exhausted_failed">
                exhausted_failed
              </option>
              <option value="stale_sending">
                stale_sending
              </option>
            </select>
          </label>

          <label className="field-label">
            Destination
            <select
              className="control-select"
              value={
                draftFilters.destination_id
                ?? ''
              }
              onChange={(event) =>
                setDraftFilters(
                  (current) => ({
                    ...current,
                    destination_id:
                      event.target.value
                      || undefined,
                  }),
                )
              }
            >
              <option value="">
                All destinations
              </option>

              {(destinations.data ?? [])
                .map((destination) => (
                  <option
                    key={destination.id}
                    value={destination.id}
                  >
                    {destination.name}
                  </option>
                ))}
            </select>
          </label>

          <label className="field-label">
            Channel
            <select
              className="control-select"
              value={draftFilters.channel ?? ''}
              onChange={(event) =>
                setDraftFilters(
                  (current) => ({
                    ...current,
                    channel:
                      event.target.value
                      || undefined,
                  }),
                )
              }
            >
              <option value="">
                All channels
              </option>

              {channelOptions.map(
                (channel) => (
                  <option
                    key={channel}
                    value={channel}
                  >
                    {channel}
                  </option>
                ),
              )}
            </select>
          </label>
        </div>

        <div className="notification-filter-actions">
          <button
            type="button"
            className="sidebar-action"
            onClick={applyFilters}
          >
            Apply filters
          </button>

          <button
            type="button"
            className="sidebar-action"
            disabled={
              activeFilterCount === 0
              && Object.values(
                draftFilters,
              ).filter(Boolean).length === 0
            }
            onClick={resetFilters}
          >
            Clear
          </button>
        </div>
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
              Page {problemCursorStack.length + 1}
              {' · '}
              {problemCount.data?.total ?? '—'}
              {' matching problem records'}
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

        <div className="ops-pagination">
          <button
            type="button"
            className="sidebar-action"
            disabled={
              problemCursorStack.length === 0
            }
            onClick={() =>
              setProblemCursorStack(
                (current) =>
                  current.slice(0, -1),
              )
            }
          >
            Previous
          </button>

          <small>
            Page {problemCursorStack.length + 1}
          </small>

          <button
            type="button"
            className="sidebar-action"
            disabled={
              !problems.data?.next_cursor
            }
            onClick={() => {
              const cursor =
                problems.data?.next_cursor

              if (!cursor) {
                return
              }

              setProblemCursorStack(
                (current) => [
                  ...current,
                  cursor,
                ],
              )
            }}
          >
            Next
          </button>
        </div>
      </section>

      <section className="panel ops-panel">
        <div className="ops-title">
          <Bell size={18} />
          <div>
            <strong>
              Delivery configuration
            </strong>
            <small>
              Destination and route summary
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
              Page {deliveryCursorStack.length + 1}
              {' · '}
              {deliveryCount.data?.total ?? '—'}
              {' matching delivery records'}
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
                    {delivery.destination_id
                      ? (
                          destinationById.get(
                            delivery.destination_id,
                          )?.name
                          ?? delivery.destination_id
                        )
                      : 'no destination'}
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
            ),
          )}
        </div>

        <div className="ops-pagination">
          <button
            type="button"
            className="sidebar-action"
            disabled={
              deliveryCursorStack.length === 0
            }
            onClick={() =>
              setDeliveryCursorStack(
                (current) =>
                  current.slice(0, -1),
              )
            }
          >
            Previous
          </button>

          <small>
            Page {deliveryCursorStack.length + 1}
          </small>

          <button
            type="button"
            className="sidebar-action"
            disabled={
              !deliveries.data?.next_cursor
            }
            onClick={() => {
              const cursor =
                deliveries.data?.next_cursor

              if (!cursor) {
                return
              }

              setDeliveryCursorStack(
                (current) => [
                  ...current,
                  cursor,
                ],
              )
            }}
          >
            Next
          </button>
        </div>
      </section>
    </>
  )
}
