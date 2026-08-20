import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  Archive,
  Bell,
  Bot,
  CheckCircle2,
  ClipboardList,
  Cpu,
  Database,
  Server,
  TriangleAlert,
} from 'lucide-react'

import {
  getAgents,
  type Agent,
} from '../api/agents'
import {
  getAuditEvents,
} from '../api/audit'
import {
  getBackupHealth,
  getBackupSchedule,
  getBackupStatus,
  getBackupStorageHealth,
} from '../api/backups'
import {
  getNotificationDeliveryHealth,
} from '../api/notifications'
import {
  getApiInfo,
  getHealth,
  getReady,
} from '../api/system'
import { useAuth } from '../auth/useAuth'
import { useWorkspaceTelemetry } from '../realtime/useWorkspaceTelemetry'

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

function averageMetric(
  agents: Agent[],
  metric:
    | 'cpu_percent'
    | 'memory_percent'
    | 'disk_percent',
) {
  const values = agents
    .map(
      (agent) =>
        agent.metrics?.[metric],
    )
    .filter(
      (value): value is number =>
        typeof value === 'number',
    )

  if (values.length === 0) {
    return null
  }

  return (
    values.reduce(
      (total, value) => total + value,
      0,
    )
    / values.length
  )
}

function percentLabel(
  value: number | null,
) {
  return value === null
    ? '—'
    : `${Math.round(value)}%`
}

function statusHealthy(
  value: string | undefined,
) {
  return value === 'healthy'
    || value === 'ok'
}

function formatDate(
  value: string | null | undefined,
) {
  if (!value) {
    return '—'
  }

  return new Date(value).toLocaleString()
}

export function Dashboard() {
  const auth = useAuth()

  const token =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

  const realtimeStatus =
    useWorkspaceTelemetry()

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

  const backups = useQuery({
    queryKey: [
      'dashboard',
      'backups',
      workspaceId,
    ],
    queryFn: async () => {
      const [
        status,
        health,
        storage,
        schedule,
      ] = await Promise.all([
        getBackupStatus(
          token!,
          workspaceId!,
        ),
        getBackupHealth(
          token!,
          workspaceId!,
        ),
        getBackupStorageHealth(
          token!,
          workspaceId!,
        ),
        getBackupSchedule(
          token!,
          workspaceId!,
        ),
      ])

      return {
        status,
        health,
        storage,
        schedule,
      }
    },
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  const notificationHealth = useQuery({
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

  const audit = useQuery({
    queryKey: [
      'dashboard',
      'audit',
      workspaceId,
    ],
    queryFn: () =>
      getAuditEvents(
        token!,
        workspaceId!,
        5,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

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

  const agentList =
    agents.data ?? []

  const onlineAgentList =
    agentList.filter(
      (agent) =>
        agent.status === 'online'
        || agent.status === 'healthy',
    )

  const onlineAgents =
    onlineAgentList.length

  const reportingAgents =
    onlineAgentList.filter(
      (agent) =>
        agent.metrics !== null,
    ).length

  const agentsHealthy =
    agents.isSuccess
    && agentList.length > 0
    && onlineAgents === agentList.length

  const averageCpu =
    averageMetric(
      onlineAgentList,
      'cpu_percent',
    )

  const averageMemory =
    averageMetric(
      onlineAgentList,
      'memory_percent',
    )

  const averageDisk =
    averageMetric(
      onlineAgentList,
      'disk_percent',
    )

  const dockerObserved =
    onlineAgentList.some(
      (agent) =>
        typeof agent.metrics?.docker
          ?.containers_total
        === 'number',
    )

  const dockerRunning =
    onlineAgentList.reduce(
      (total, agent) =>
        total
        + (
          agent.metrics?.docker
            ?.containers_running
          ?? 0
        ),
      0,
    )

  const dockerTotal =
    onlineAgentList.reduce(
      (total, agent) =>
        total
        + (
          agent.metrics?.docker
            ?.containers_total
          ?? 0
        ),
      0,
    )

  const backupData =
    backups.data

  const backupHealthy =
    backups.isSuccess
    && statusHealthy(
      backupData?.status.status,
    )
    && statusHealthy(
      backupData?.health.status,
    )
    && backupData?.storage.healthy === true

  const notificationHealthy =
    notificationHealth.isSuccess
    && statusHealthy(
      notificationHealth.data?.status,
    )

  const notificationCounts =
    notificationHealth.data?.total

  const auditEvents =
    audit.data ?? []

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

        <StatusCard
          title="Agents"
          value={
            agents.isLoading
              ? 'Loading'
              : agents.isError
                ? 'Unavailable'
                : `${onlineAgents} / ${agentList.length} online`
          }
          healthy={agentsHealthy}
          detail={
            agents.isSuccess
              ? `${reportingAgents} reporting telemetry`
              : undefined
          }
        />

        <StatusCard
          title="Realtime"
          value={
            realtimeStatus === 'connected'
              ? 'Connected'
              : realtimeStatus
          }
          healthy={
            realtimeStatus === 'connected'
          }
          detail="Workspace telemetry"
        />

        <StatusCard
          title="Backups"
          value={
            backups.isLoading
              ? 'Loading'
              : backups.isError
                ? 'Unavailable'
                : backupHealthy
                  ? 'Healthy'
                  : 'Degraded'
          }
          healthy={backupHealthy}
          detail={
            backupData
              ? `${backupData.status.failed_jobs} failed jobs · storage ${
                  backupData.storage.healthy
                    ? 'healthy'
                    : 'unhealthy'
                }`
              : undefined
          }
        />

        <StatusCard
          title="Notifications"
          value={
            notificationHealth.isLoading
              ? 'Loading'
              : notificationHealth.isError
                ? 'Unavailable'
                : notificationHealthy
                  ? 'Healthy'
                  : 'Degraded'
          }
          healthy={notificationHealthy}
          detail={
            notificationCounts
              ? `${notificationCounts.failed} failed · ${notificationCounts.pending} pending`
              : undefined
          }
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
            <div>
              <dt>Build</dt>
              <dd>
                {api.data?.build_revision
                  ? api.data.build_revision.slice(
                      0,
                      12,
                    )
                  : '—'}
              </dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <div className="panel__title">
            <Cpu size={20} />
            <h2>Infrastructure</h2>
          </div>

          <div className="readiness-row">
            <span>CPU average</span>
            <strong>
              {percentLabel(averageCpu)}
            </strong>
          </div>

          <div className="readiness-row">
            <span>Memory average</span>
            <strong>
              {percentLabel(
                averageMemory,
              )}
            </strong>
          </div>

          <div className="readiness-row">
            <span>Disk average</span>
            <strong>
              {percentLabel(averageDisk)}
            </strong>
          </div>

          <div className="readiness-row">
            <span>Docker containers</span>
            <strong>
              {dockerObserved
                ? `${dockerRunning} / ${dockerTotal}`
                : '—'}
            </strong>
          </div>
        </article>

        <article className="panel">
          <div className="panel__title">
            <Bot size={20} />
            <h2>Agents</h2>
          </div>

          {agents.isLoading && (
            <div className="placeholder">
              Loading agents…
            </div>
          )}

          {agents.isError && (
            <div className="placeholder">
              Agent status unavailable.
            </div>
          )}

          {agents.isSuccess
            && agentList.length === 0
            && (
              <div className="placeholder">
                No enrolled agents.
              </div>
            )}

          {agents.isSuccess
            && agentList.length > 0
            && (
              <>
                <div className="readiness-row">
                  <span>Online</span>
                  <strong>
                    {onlineAgents}
                    {' / '}
                    {agentList.length}
                  </strong>
                </div>

                <div className="readiness-row">
                  <span>Telemetry</span>
                  <strong>
                    {reportingAgents}
                    {' / '}
                    {agentList.length}
                  </strong>
                </div>

                <div className="readiness-row">
                  <span>Realtime</span>
                  <strong>
                    {realtimeStatus.toUpperCase()}
                  </strong>
                </div>

                {agentList
                  .slice(0, 4)
                  .map((agent) => (
                    <div
                      className="readiness-row"
                      key={agent.id}
                    >
                      <span>
                        {agent.hostname}
                      </span>
                      <strong>
                        {agent.status.toUpperCase()}
                      </strong>
                    </div>
                  ))}
              </>
            )}
        </article>

        <article className="panel">
          <div className="panel__title">
            <Archive size={20} />
            <h2>Backup protection</h2>
          </div>

          {backups.isLoading && (
            <div className="placeholder">
              Loading backup health…
            </div>
          )}

          {backups.isError && (
            <div className="placeholder">
              Backup health unavailable.
            </div>
          )}

          {backupData && (
            <>
              <div className="readiness-row">
                <span>Status</span>
                <strong>
                  {backupData.status.status.toUpperCase()}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Storage</span>
                <strong>
                  {backupData.storage.healthy
                    ? 'HEALTHY'
                    : 'UNHEALTHY'}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Failed jobs</span>
                <strong>
                  {backupData.status.failed_jobs}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Last verified</span>
                <strong>
                  {formatDate(
                    backupData.health
                      .last_verified_at,
                  )}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Schedule</span>
                <strong>
                  {backupData.schedule
                    ? backupData.schedule.enabled
                      ? 'ENABLED'
                      : 'DISABLED'
                    : 'NOT CONFIGURED'}
                </strong>
              </div>
            </>
          )}
        </article>

        <article className="panel">
          <div className="panel__title">
            <Bell size={20} />
            <h2>Notification delivery</h2>
          </div>

          {notificationHealth.isLoading && (
            <div className="placeholder">
              Loading delivery health…
            </div>
          )}

          {notificationHealth.isError && (
            <div className="placeholder">
              Delivery health unavailable.
            </div>
          )}

          {notificationHealth.data && (
            <>
              <div className="readiness-row">
                <span>Status</span>
                <strong>
                  {notificationHealth.data.status
                    .toUpperCase()}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Failed</span>
                <strong>
                  {notificationHealth.data
                    .total.failed}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Retryable</span>
                <strong>
                  {notificationHealth.data
                    .total.retryable_failed}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Stale sending</span>
                <strong>
                  {notificationHealth.data
                    .total.stale_sending}
                </strong>
              </div>

              <div className="readiness-row">
                <span>Issues</span>
                <strong>
                  {notificationHealth.data
                    .issues.length}
                </strong>
              </div>
            </>
          )}
        </article>

        <article className="panel">
          <div className="panel__title">
            <ClipboardList size={20} />
            <h2>Recent audit</h2>
          </div>

          {audit.isLoading && (
            <div className="placeholder">
              Loading audit events…
            </div>
          )}

          {audit.isError && (
            <div className="placeholder">
              Audit history unavailable.
            </div>
          )}

          {audit.isSuccess
            && auditEvents.length === 0
            && (
              <div className="placeholder">
                No audit events.
              </div>
            )}

          {auditEvents.map((event) => (
            <div
              className="readiness-row"
              key={event.id}
            >
              <span>
                {event.action}
              </span>
              <strong>
                {formatDate(
                  event.created_at,
                )}
              </strong>
            </div>
          ))}
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
