import {
  Activity,
  Bot,
  Clock3,
  Cpu,
  HardDrive,
  MemoryStick,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import {
  getAgents,
  type Agent,
} from '../api/agents'
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
}: {
  agent: Agent
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
    </article>
  )
}

export function Agents() {
  const auth = useAuth()
  const realtime =
    useWorkspaceTelemetry()

  const token =
    auth.tokens?.access_token

  const agents = useQuery({
    queryKey: [
      'agents',
      auth.workspace?.id,
    ],
    queryFn: () =>
      getAgents(token!),
    enabled: Boolean(
      token && auth.workspace,
    ),
    refetchInterval: 15_000,
  })

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
          />
        ))}
      </section>
    </>
  )
}
