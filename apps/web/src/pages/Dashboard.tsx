import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  Bot,
  CheckCircle2,
  Cpu,
  Database,
  Server,
  TriangleAlert,
} from 'lucide-react'

import {
  getApiInfo,
  getHealth,
  getReady,
} from '../api/system'

type StatusCardProps = {
  title: string
  value: string
  healthy: boolean
  detail?: string
}

function StatusCard({
  title,
  value,
  healthy,
  detail,
}: StatusCardProps) {
  return (
    <article className="status-card">
      <div className="status-card__header">
        <span>{title}</span>
        {healthy ? (
          <CheckCircle2 size={18} aria-label="healthy" />
        ) : (
          <TriangleAlert size={18} aria-label="unhealthy" />
        )}
      </div>

      <strong>{value}</strong>

      {detail && <small>{detail}</small>}
    </article>
  )
}

export function Dashboard() {
  const api = useQuery({
    queryKey: ['system', 'api'],
    queryFn: getApiInfo,
    refetchInterval: 10_000,
    retry: false,
  })

  const health = useQuery({
    queryKey: ['system', 'health'],
    queryFn: getHealth,
    refetchInterval: 5_000,
    retry: false,
  })

  const ready = useQuery({
    queryKey: ['system', 'ready'],
    queryFn: getReady,
    refetchInterval: 5_000,
    retry: false,
  })

  const apiOnline = api.isSuccess
  const serviceHealthy =
    health.data?.status === 'ok'

  const databaseHealthy =
    ready.data?.checks.database === true

  const redisHealthy =
    ready.data?.checks.redis === true

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Infrastructure overview</p>
          <h1>Control Center</h1>
          <p>
            Live status from the AI-project SRV backend.
          </p>
        </div>

        <div
          className={
            serviceHealthy
              ? 'system-pill system-pill--online'
              : 'system-pill'
          }
        >
          <Activity size={16} />
          {serviceHealthy ? 'ONLINE' : 'DEGRADED'}
        </div>
      </header>

      <section className="status-grid">
        <StatusCard
          title="API"
          value={apiOnline ? 'Online' : 'Unavailable'}
          healthy={apiOnline}
          detail={
            api.data
              ? `${api.data.name} · ${api.data.version}`
              : undefined
          }
        />

        <StatusCard
          title="Service"
          value={serviceHealthy ? 'Healthy' : 'Unavailable'}
          healthy={serviceHealthy}
          detail={health.data?.environment}
        />

        <StatusCard
          title="PostgreSQL"
          value={databaseHealthy ? 'Ready' : 'Not ready'}
          healthy={databaseHealthy}
        />

        <StatusCard
          title="Redis"
          value={redisHealthy ? 'Ready' : 'Not ready'}
          healthy={redisHealthy}
        />
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel__title">
            <Server size={20} />
            <h2>Platform</h2>
          </div>

          <dl className="details">
            <div>
              <dt>Version</dt>
              <dd>{api.data?.version ?? '—'}</dd>
            </div>
            <div>
              <dt>Phase</dt>
              <dd>{api.data?.phase ?? '—'}</dd>
            </div>
            <div>
              <dt>Environment</dt>
              <dd>{health.data?.environment ?? '—'}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <div className="panel__title">
            <Cpu size={20} />
            <h2>Infrastructure</h2>
          </div>

          <div className="placeholder">
            Resource telemetry will appear here next.
          </div>
        </article>

        <article className="panel">
          <div className="panel__title">
            <Bot size={20} />
            <h2>Agents</h2>
          </div>

          <div className="placeholder">
            Linux Agent status will appear here next.
          </div>
        </article>

        <article className="panel">
          <div className="panel__title">
            <Database size={20} />
            <h2>Readiness</h2>
          </div>

          <div className="readiness-row">
            <span>PostgreSQL</span>
            <strong>
              {databaseHealthy ? 'READY' : 'NOT READY'}
            </strong>
          </div>

          <div className="readiness-row">
            <span>Redis</span>
            <strong>
              {redisHealthy ? 'READY' : 'NOT READY'}
            </strong>
          </div>
        </article>
      </section>
    </>
  )
}
