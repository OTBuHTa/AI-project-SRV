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
  getAgents,
  type Agent,
  rotateAgentToken,
} from '../api/agents'
import {
  getActiveAgentLifecycleAlerts,
  getAgentLifecycleAlerts,
  getAgentTokenLifecycleDiagnostics,
} from '../api/monitoring'
import { useAuth } from '../auth/useAuth'
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
  onRotate,
}: {
  agent: Agent
  rotating: boolean
  onRotate: (agent: Agent) => void
}) {
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
          disabled={
            rotating
            || agent.status === 'revoked'
          }
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
            onRotate={(targetAgent) =>
              rotateToken.mutate(
                targetAgent,
              )
            }
          />
        ))}
      </section>
    </>
  )
}
