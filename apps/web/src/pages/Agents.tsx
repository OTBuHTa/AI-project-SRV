import {
  useState,
} from 'react'
import {
  Activity,
  Bot,
  Clock3,
  Cpu,
  HardDrive,
  MemoryStick,
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react'
import {
  useQuery,
  useMutation,
} from '@tanstack/react-query'

import {
  createEnrollmentToken,
  getAgents,
  type Agent,
  revokeAgent,
  rotateAgentToken,
} from '../api/agents'
import {
  evaluateAgentStatuses,
  getActiveAgentLifecycleAlerts,
  getAgentLifecycleAlerts,
  getAgentTokenLifecycleDiagnostics,
} from '../api/monitoring'
import { useAuth } from '../auth/useAuth'
import { hasPermission } from '../auth/permissions'
import { useWorkspaceTelemetry } from '../realtime/useWorkspaceTelemetry'

function percent(
  value: number | undefined,
) {
  return value === undefined
    ? '—'
    : `${value.toFixed(1)}%`
}

function uptime(
  seconds: number | undefined,
) {
  if (seconds === undefined) {
    return '—'
  }

  const days = Math.floor(
    seconds / 86400,
  )

  const hours = Math.floor(
    (seconds % 86400) / 3600,
  )

  return `${days}d ${hours}h`
}

function lastSeen(
  value: string | null,
) {
  if (!value) {
    return 'Never'
  }

  return new Date(value).toLocaleString()
}

function AgentCard({
  agent,
  rotating,
  revoking,
  onRotate,
  onRevoke,
}: {
  agent: Agent
  rotating: boolean
  revoking: boolean
  onRotate: (agent: Agent) => void
  onRevoke: (agent: Agent) => void
}) {
  const auth = useAuth()

  const canRotateAgent =
    hasPermission(
      auth.workspace?.role,
      'agent.update',
    )

  const canRevokeAgent =
    hasPermission(
      auth.workspace?.role,
      'agent.revoke',
    )

  const metrics = agent.metrics

  return (
    <article className="agent-card">
      <header className="agent-card__header">
        <div>
          <div className="agent-title">
            <Bot size={19} />
            <strong>{agent.hostname}</strong>
          </div>

          <small>
            {agent.agent_type}
            {' · '}
            {agent.version}
          </small>
        </div>

        <span
          className={
            agent.status === 'online'
            || agent.status === 'healthy'
              ? 'status-badge status-badge--ok'
              : 'status-badge'
          }
        >
          {agent.status}
        </span>
      </header>

      <div className="metric-grid">
        <div className="metric-item">
          <Cpu size={17} />
          <span>CPU</span>
          <strong>
            {percent(metrics?.cpu_percent)}
          </strong>
        </div>

        <div className="metric-item">
          <MemoryStick size={17} />
          <span>RAM</span>
          <strong>
            {percent(metrics?.memory_percent)}
          </strong>
        </div>

        <div className="metric-item">
          <HardDrive size={17} />
          <span>Disk</span>
          <strong>
            {percent(metrics?.disk_percent)}
          </strong>
        </div>

        <div className="metric-item">
          <Clock3 size={17} />
          <span>Uptime</span>
          <strong>
            {uptime(metrics?.uptime_seconds)}
          </strong>
        </div>
      </div>

      <div className="agent-details">
        <div>
          <span>Resource</span>
          <code>{agent.resource_id}</code>
        </div>

        <div>
          <span>Last heartbeat</span>
          <strong>
            {lastSeen(agent.last_seen_at)}
          </strong>
        </div>

        <div>
          <span>Capabilities</span>
          <strong>
            {agent.capabilities.length}
          </strong>
        </div>

        <div>
          <span>Docker</span>
          <strong>
            {metrics?.docker?.available
              ? (
                  `${metrics.docker.containers_running ?? 0}`
                  + '/'
                  + `${metrics.docker.containers_total ?? 0}`
                )
              : 'Unavailable'}
          </strong>
        </div>
      </div>

      <div className="notification-filter-actions">
        <button
          type="button"
          className="sidebar-action"
          disabled={!canRotateAgent || (
            rotating
            || revoking
            || agent.status === 'revoked'
          )}
          onClick={() => {
            const confirmed = window.confirm(
              'Rotate the token for '
              + agent.hostname
              + '? The current token will become '
              + 'invalid immediately.',
            )

            if (confirmed) {
              onRotate(agent)
            }
          }}
        >
          {rotating
            ? 'Rotating…'
            : 'Rotate agent token'}
        </button>

        <button
          type="button"
          className="sidebar-action"
          disabled={!canRevokeAgent || (
            rotating
            || revoking
            || agent.status === 'revoked'
          )}
          onClick={() => {
            const confirmed = window.confirm(
              'Revoke agent '
              + agent.hostname
              + '? This will invalidate its '
              + 'credentials, cancel any pending '
              + 'token rotation and mark the '
              + 'linked resource offline.',
            )

            if (confirmed) {
              onRevoke(agent)
            }
          }}
        >
          {agent.status === 'revoked'
            ? 'Agent revoked'
            : revoking
              ? 'Revoking…'
              : 'Revoke agent'}
        </button>
      </div>
    </article>
  )
}

export function Agents() {
  const auth = useAuth()
  const realtime =
    useWorkspaceTelemetry()

  const token =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

  const canEvaluateAgent =
    hasPermission(
      auth.workspace?.role,
      'agent.read',
    )

  const canInstallAgent =
    hasPermission(
      auth.workspace?.role,
      'agent.install',
    )


  const [
    statusEvaluation,
    setStatusEvaluation,
  ] = useState<{
    evaluated: number
    changed: number
    offlineAfterSeconds: number
  } | null>(null)

  const [
    enrollmentCredential,
    setEnrollmentCredential,
  ] = useState<{
    name: string
    agentType: string
    enrollmentToken: string
    expiresAt: string
  } | null>(null)

  const [
    rotatedCredential,
    setRotatedCredential,
  ] = useState<{
    agentId: string
    hostname: string
    agentToken: string
    expiresAt: string
    rotatedAt: string
  } | null>(null)

  const [
    revokedAgent,
    setRevokedAgent,
  ] = useState<{
    agentId: string
    hostname: string
    revokedAt: string
  } | null>(null)

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

  const lifecycle = useQuery({
    queryKey: [
      'agent-lifecycle',
      workspaceId,
    ],
    queryFn: async () => {
      const [
        diagnostics,
        activeAlerts,
        alertHistory,
      ] = await Promise.all([
        getAgentTokenLifecycleDiagnostics(
          token!,
          workspaceId!,
        ),
        getActiveAgentLifecycleAlerts(
          token!,
          workspaceId!,
        ),
        getAgentLifecycleAlerts(
          token!,
          workspaceId!,
        ),
      ])

      return {
        diagnostics,
        activeAlerts,
        alertHistory,
      }
    },
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  const evaluateStatuses =
    useMutation({
      mutationFn: () =>
        evaluateAgentStatuses(
          token!,
          workspaceId!,
        ),
      onMutate: () => {
        setStatusEvaluation(null)
      },
      onSuccess: (result) => {
        setStatusEvaluation({
          evaluated: result.evaluated,
          changed: result.changed,
          offlineAfterSeconds:
            result.offline_after_seconds,
        })

        void agents.refetch()
      },
    })

  const createEnrollment =
    useMutation({
      mutationFn: (payload: {
        name: string
        agent_type: string
        ttl_minutes: number
      }) =>
        createEnrollmentToken(
          token!,
          workspaceId!,
          payload,
        ),
      onMutate: () => {
        setEnrollmentCredential(null)
      },
      onSuccess: (result, payload) => {
        setEnrollmentCredential({
          name: payload.name,
          agentType: payload.agent_type,
          enrollmentToken: result.token,
          expiresAt: result.expires_at,
        })
      },
    })

  const rotateToken = useMutation({
    mutationFn: (agent: Agent) =>
      rotateAgentToken(
        token!,
        workspaceId!,
        agent.id,
      ),
    onMutate: () => {
      setRotatedCredential(null)
    },
    onSuccess: (result, agent) => {
      setRotatedCredential({
        agentId: agent.id,
        hostname: agent.hostname,
        agentToken: result.agent_token,
        expiresAt:
          result.agent_token_expires_at,
        rotatedAt:
          result.token_rotated_at,
      })

      void agents.refetch()
      void lifecycle.refetch()
    },
  })

  const revokeAgentMutation = useMutation({
    mutationFn: (agent: Agent) =>
      revokeAgent(
        token!,
        workspaceId!,
        agent.id,
      ),
    onMutate: () => {
      setRevokedAgent(null)
    },
    onSuccess: (result, agent) => {
      setRevokedAgent({
        agentId: result.agent_id,
        hostname: agent.hostname,
        revokedAt: result.revoked_at,
      })

      if (
        rotatedCredential?.agentId
        === agent.id
      ) {
        setRotatedCredential(null)
      }

      void agents.refetch()
      void lifecycle.refetch()
    },
  })

  const lifecycleData =
    lifecycle.data

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Infrastructure agents
          </p>
          <h1>Agents</h1>
          <p>
            Live heartbeat and system telemetry.
          </p>
        </div>

        <div
          className={
            realtime === 'connected'
              ? 'system-pill system-pill--online'
              : 'system-pill'
          }
        >
          <Activity size={16} />
          WS {realtime.toUpperCase()}
        </div>
      </header>

      <section className="panel ops-panel">
        <div className="ops-title">
          <Activity size={18} />
          <div>
            <strong>
              Agent status evaluation
            </strong>
            <small>
              Reconcile linked resource status
              from current agent heartbeat state.
            </small>
          </div>
        </div>

        <div className="ops-details">
          <div>
            <span>Offline threshold</span>
            <strong>
              {statusEvaluation
                ? (
                    `${statusEvaluation
                      .offlineAfterSeconds}s`
                  )
                : '90s'}
            </strong>
          </div>

          <div>
            <span>Last evaluated</span>
            <strong>
              {statusEvaluation
                ? statusEvaluation.evaluated
                : '—'}
            </strong>
          </div>

          <div>
            <span>Resources changed</span>
            <strong>
              {statusEvaluation
                ? statusEvaluation.changed
                : '—'}
            </strong>
          </div>
        </div>

        <div className="notification-filter-actions">
          <button
            type="button"
            className="primary-button"
            disabled={
              !canEvaluateAgent
              || !token
              || !workspaceId
              || evaluateStatuses.isPending
            }
            onClick={() =>
              evaluateStatuses.mutate()
            }
          >
            {evaluateStatuses.isPending
              ? 'Evaluating…'
              : 'Evaluate agent status'}
          </button>
        </div>
      </section>

      {evaluateStatuses.isError && (
        <div className="auth-error">
          Agent status evaluation failed.
        </div>
      )}

      {statusEvaluation && (
        <div className="ops-success">
          Evaluated {statusEvaluation.evaluated}
          {' agent(s); updated '}
          {statusEvaluation.changed}
          {' linked resource(s). Offline threshold: '}
          {statusEvaluation.offlineAfterSeconds}
          {' seconds.'}
        </div>
      )}

      <section className="panel ops-panel">
        <div className="ops-title">
          <ShieldCheck size={18} />
          <div>
            <strong>
              Agent enrollment
            </strong>
            <small>
              Create a one-time enrollment token
              for a new infrastructure agent.
            </small>
          </div>
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault()

            const form =
              new FormData(
                event.currentTarget,
              )

            const name =
              String(
                form.get('name') ?? '',
              ).trim()

            const agentType =
              String(
                form.get('agent_type')
                  ?? '',
              ).trim()

            const ttlMinutes =
              Number(
                form.get('ttl_minutes'),
              )

            if (
              name.length < 1
              || name.length > 160
              || !/^[a-z0-9_-]{2,32}$/.test(
                agentType,
              )
              || !Number.isInteger(
                ttlMinutes,
              )
              || ttlMinutes < 5
              || ttlMinutes > 1440
            ) {
              return
            }

            createEnrollment.mutate({
              name,
              agent_type: agentType,
              ttl_minutes: ttlMinutes,
            })
          }}
        >
          <div className="notification-filter-grid">
            <label className="field-label">
              Name

              <input
                className="control-input"
                type="text"
                name="name"
                minLength={1}
                maxLength={160}
                placeholder="srv-agent-01"
                required
              />
            </label>

            <label className="field-label">
              Agent type

              <input
                className="control-input"
                type="text"
                name="agent_type"
                defaultValue="linux"
                minLength={2}
                maxLength={32}
                pattern="[a-z0-9_-]{2,32}"
                required
              />
            </label>

            <label className="field-label">
              TTL minutes

              <input
                className="control-input"
                type="number"
                name="ttl_minutes"
                min={5}
                max={1440}
                step={1}
                defaultValue={30}
                required
              />
            </label>
          </div>

          <div className="notification-filter-actions">
            <button
              type="submit"
              className="primary-button"
              disabled={!canInstallAgent || (
                !token
                || !workspaceId
                || createEnrollment.isPending
              )}
            >
              {createEnrollment.isPending
                ? 'Creating…'
                : 'Create enrollment token'}
            </button>
          </div>
        </form>
      </section>

      {createEnrollment.isError && (
        <div className="auth-error">
          Enrollment token creation failed.
        </div>
      )}

      {enrollmentCredential && (
        <section className="panel ops-panel">
          <div className="ops-title">
            <ShieldCheck size={18} />

            <div>
              <strong>
                Enrollment token
              </strong>

              <small>
                {enrollmentCredential.name}
                {' · '}
                {enrollmentCredential.agentType}
                {' · shown only in this page state'}
              </small>
            </div>
          </div>

          <div className="ops-details">
            <div>
              <span>Name</span>
              <strong>
                {enrollmentCredential.name}
              </strong>
            </div>

            <div>
              <span>Agent type</span>
              <strong>
                {enrollmentCredential.agentType}
              </strong>
            </div>

            <div>
              <span>Expires</span>
              <strong>
                {lastSeen(
                  enrollmentCredential.expiresAt,
                )}
              </strong>
            </div>
          </div>

          <div className="ops-empty">
            Save this enrollment token before
            dismissing it. The token is returned
            only when it is created and can enroll
            one agent before expiration.
          </div>

          <code>
            {
              enrollmentCredential
                .enrollmentToken
            }
          </code>

          <div className="notification-filter-actions">
            <button
              type="button"
              className="sidebar-action"
              onClick={() =>
                setEnrollmentCredential(null)
              }
            >
              Dismiss token
            </button>
          </div>
        </section>
      )}

      {lifecycle.isError && (
        <div className="auth-error">
          Failed to load agent lifecycle
          diagnostics.
        </div>
      )}


      {rotateToken.isError && (
        <div className="auth-error">
          Agent token rotation failed.
        </div>
      )}


      {revokeAgentMutation.isError && (
        <div className="auth-error">
          Agent revocation failed.
        </div>
      )}

      {revokedAgent && (
        <div className="ops-success">
          Agent {revokedAgent.hostname}
          {' revoked at '}
          {lastSeen(revokedAgent.revokedAt)}.
          {' Resource marked offline.'}
        </div>
      )}

      {rotatedCredential && (
        <section className="panel ops-panel">
          <div className="ops-title">
            <ShieldCheck size={18} />
            <div>
              <strong>
                New agent token
              </strong>
              <small>
                {rotatedCredential.hostname}
                {' · shown only in this page state'}
              </small>
            </div>
          </div>

          <div className="ops-details">
            <div>
              <span>Agent</span>
              <code>
                {rotatedCredential.agentId}
              </code>
            </div>

            <div>
              <span>Rotated</span>
              <strong>
                {lastSeen(
                  rotatedCredential.rotatedAt,
                )}
              </strong>
            </div>

            <div>
              <span>Expires</span>
              <strong>
                {lastSeen(
                  rotatedCredential.expiresAt,
                )}
              </strong>
            </div>
          </div>

          <div className="ops-empty">
            Save this token in the agent
            configuration before dismissing it.
            The previous token is no longer valid.
          </div>

          <code>
            {rotatedCredential.agentToken}
          </code>

          <div className="notification-filter-actions">
            <button
              type="button"
              className="sidebar-action"
              onClick={() =>
                setRotatedCredential(null)
              }
            >
              Dismiss token
            </button>
          </div>
        </section>
      )}

      <section className="ops-stat-grid">
        <article className="ops-stat">
          <span>Token lifecycle</span>
          <strong>
            {lifecycleData?.diagnostics.status
              ?? '—'}
          </strong>
          <small>
            {lifecycleData
              ? (
                  `${lifecycleData.diagnostics.issues.length}`
                  + ' issue(s)'
                )
              : 'Loading…'}
          </small>
        </article>

        <article className="ops-stat">
          <span>Pending rotations</span>
          <strong>
            {lifecycleData?.diagnostics
              .pending_rotations ?? '—'}
          </strong>
          <small>
            of{' '}
            {lifecycleData?.diagnostics
              .agents_total ?? '—'} agents
          </small>
        </article>

        <article className="ops-stat">
          <span>Expired rotations</span>
          <strong>
            {lifecycleData?.diagnostics
              .expired_pending_rotations
              ?? '—'}
          </strong>
          <small>
            Pending beyond prepare TTL
          </small>
        </article>

        <article className="ops-stat">
          <span>Incomplete rotations</span>
          <strong>
            {lifecycleData?.diagnostics
              .incomplete_pending_rotations
              ?? '—'}
          </strong>
          <small>
            Inconsistent pending state
          </small>
        </article>
      </section>

      <section className="ops-grid">
        <article className="panel ops-panel">
          <div className="ops-title">
            <ShieldCheck size={18} />
            <strong>Token lifecycle state</strong>
          </div>

          <div className="ops-details">
            <div>
              <span>Agents</span>
              <strong>
                {lifecycleData?.diagnostics
                  .agents_total ?? '—'}
              </strong>
            </div>

            <div>
              <span>Revoked with pending</span>
              <strong>
                {lifecycleData?.diagnostics
                  .revoked_with_pending_rotation
                  ?? '—'}
              </strong>
            </div>

            <div>
              <span>Oldest pending</span>
              <strong>
                {lifecycleData
                  ? lastSeen(
                      lifecycleData.diagnostics
                        .oldest_pending_prepared_at,
                    )
                  : '—'}
              </strong>
            </div>

            <div>
              <span>Observed</span>
              <strong>
                {lifecycleData
                  ? lastSeen(
                      lifecycleData.diagnostics
                        .observed_at,
                    )
                  : '—'}
              </strong>
            </div>
          </div>
        </article>

        <article className="panel ops-panel">
          <div className="ops-title">
            <TriangleAlert size={18} />
            <strong>
              Active lifecycle alerts
            </strong>
          </div>

          {lifecycle.isLoading && (
            <div className="ops-empty">
              Loading lifecycle alerts…
            </div>
          )}

          {lifecycleData
            && lifecycleData.activeAlerts.length
              === 0
            && (
              <div className="ops-empty">
                No active lifecycle alerts.
              </div>
            )}

          <div className="ops-list">
            {lifecycleData?.activeAlerts.map(
              (alert) => (
                <article
                  className="ops-row"
                  key={alert.id}
                >
                  <div className="ops-row__main">
                    <div className="ops-row__heading">
                      <TriangleAlert
                        size={16}
                      />

                      <strong>
                        {alert.code}
                      </strong>

                      <span className="status-badge">
                        {alert.severity}
                      </span>
                    </div>

                    <small>
                      first seen{' '}
                      {lastSeen(
                        alert.first_seen_at,
                      )}
                      {' · last seen '}
                      {lastSeen(
                        alert.last_seen_at,
                      )}
                    </small>
                  </div>

                  <span>
                    {alert.message}
                  </span>
                </article>
              ),
            )}
          </div>
        </article>
      </section>

      <section className="panel ops-panel">
        <div className="ops-title">
          <Clock3 size={18} />
          <div>
            <strong>
              Lifecycle alert history
            </strong>
            <small>
              Latest workspace lifecycle events
            </small>
          </div>
        </div>

        {lifecycle.isLoading && (
          <div className="ops-empty">
            Loading lifecycle history…
          </div>
        )}

        {lifecycleData
          && lifecycleData.alertHistory.length
            === 0
          && (
            <div className="ops-empty">
              No lifecycle alert events recorded.
            </div>
          )}

        <div className="ops-list">
          {lifecycleData?.alertHistory.map(
            (alert) => (
              <article
                className="ops-row"
                key={alert.id}
              >
                <div className="ops-row__main">
                  <div className="ops-row__heading">
                    <TriangleAlert size={16} />

                    <strong>
                      {alert.code}
                    </strong>

                    <span className="status-badge">
                      {alert.severity}
                    </span>

                    <span
                      className={
                        alert.active
                          ? 'status-badge'
                          : (
                              'status-badge '
                              + 'status-badge--ok'
                            )
                      }
                    >
                      {alert.active
                        ? 'active'
                        : 'resolved'}
                    </span>
                  </div>

                  <small>
                    first seen{' '}
                    {lastSeen(
                      alert.first_seen_at,
                    )}
                    {' · last seen '}
                    {lastSeen(
                      alert.last_seen_at,
                    )}
                  </small>
                </div>

                <span>
                  {alert.message}
                </span>

                <small>
                  resolved{' '}
                  {lastSeen(
                    alert.resolved_at,
                  )}
                </small>
              </article>
            ),
          )}
        </div>
      </section>

      {agents.isLoading && (
        <div className="panel">
          Loading agents…
        </div>
      )}

      {agents.isError && (
        <div className="auth-error">
          Failed to load agents.
        </div>
      )}

      {agents.data?.length === 0 && (
        <div className="panel empty-state">
          <Bot size={28} />
          <strong>No active agents</strong>
          <span>
            Enroll a Linux agent to start
            receiving telemetry.
          </span>
        </div>
      )}

      <section className="agent-list">
        {agents.data?.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            rotating={
              rotateToken.isPending
              && rotateToken.variables?.id
                === agent.id
            }
            revoking={
              revokeAgentMutation.isPending
              && revokeAgentMutation.variables?.id
                === agent.id
            }
            onRotate={(targetAgent) =>
              rotateToken.mutate(
                targetAgent,
              )
            }
            onRevoke={(targetAgent) =>
              revokeAgentMutation.mutate(
                targetAgent,
              )
            }
          />
        ))}
      </section>
    </>
  )
}
