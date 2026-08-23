import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
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
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react'

import {
  getActionPlans,
} from '../api/actions'
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
import { hasPermission } from '../auth/permissions'
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

  const role =
    auth.workspace?.role

  const canReadWorkspace =
    hasPermission(
      role,
      'workspace.read',
    )

  const canReadAgents =
    hasPermission(
      role,
      'agent.read',
    )

  const canReadActions =
    hasPermission(
      role,
      'action.read',
    )

  const canReadAudit =
    hasPermission(
      role,
      'audit.read',
    )

  const realtimeStatus =
    useWorkspaceTelemetry(
      canReadAgents,
    )

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
      token
      && workspaceId
      && canReadAgents,
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
      token
      && workspaceId
      && canReadWorkspace,
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
      token
      && workspaceId
      && canReadWorkspace,
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
      token
      && workspaceId
      && canReadAudit,
    ),
    refetchInterval: 15_000,
  })

  const actions = useQuery({
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
      token
      && workspaceId
      && canReadActions,
    ),
    refetchInterval: 10_000,
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

  const actionPlans =
    actions.data ?? []

  const awaitingApproval =
    actionPlans.filter(
      (plan) =>
        plan.status === 'pending_approval',
    ).length

  const queuedActions =
    actionPlans.filter(
      (plan) =>
        plan.status === 'queued',
    ).length

  const verifyingActions =
    actionPlans.filter(
      (plan) =>
        plan.status === 'verifying',
    ).length

  const failedActions =
    actionPlans.filter(
      (plan) =>
        plan.status === 'failed'
        || plan.status === 'verification_failed',
    ).length

  const executingActions =
    actionPlans.filter(
      (plan) =>
        plan.status === 'executing',
    ).length

  const rejectedActions =
    actionPlans.filter(
      (plan) =>
        plan.status === 'rejected',
    ).length

  const nonOnlineAgents =
    Math.max(
      agentList.length - onlineAgents,
      0,
    )

  const notificationIssues =
    notificationHealth.data
      ?.issues.length
    ?? 0

  const notificationFailed =
    notificationHealth.data
      ?.total.failed
    ?? 0

  const notificationStale =
    notificationHealth.data
      ?.total.stale_sending
    ?? 0

  const backupFailedJobs =
    backupData?.status.failed_jobs
    ?? 0

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

      {(canReadAgents || canReadActions || canReadWorkspace) && (
        <section className="ops-stat-grid">
          {canReadAgents && (
            <article className="ops-stat">
              <span>Agents online</span>

              <strong>
                {agents.isSuccess
                  ? `${onlineAgents} / ${agentList.length}`
                  : '—'}
              </strong>

              <small>
                {agents.isSuccess
                  ? `${reportingAgents} reporting telemetry · ${nonOnlineAgents} non-online`
                  : 'Agent state unavailable'}
              </small>
            </article>
          )}

          {canReadActions && (
            <article className="ops-stat">
              <span>Pending approval</span>

              <strong>
                {actions.isSuccess
                  ? awaitingApproval
                  : '—'}
              </strong>

              <small>
                {actions.isSuccess
                  ? `${queuedActions} queued · ${executingActions} executing · ${verifyingActions} verifying`
                  : 'Action lifecycle unavailable'}
              </small>
            </article>
          )}

          {canReadWorkspace && (
            <article className="ops-stat">
              <span>Delivery issues</span>

              <strong>
                {notificationHealth.isSuccess
                  ? notificationIssues
                  : '—'}
              </strong>

              <small>
                {notificationHealth.isSuccess
                  ? `${notificationFailed} failed · ${notificationStale} stale sending`
                  : 'Notification health unavailable'}
              </small>
            </article>
          )}

          {canReadWorkspace && (
            <article className="ops-stat">
              <span>Backup failures</span>

              <strong>
                {backups.isSuccess
                  ? backupFailedJobs
                  : '—'}
              </strong>

              <small>
                {backups.isSuccess
                  ? `Storage ${
                      backupData?.storage.healthy
                        ? 'healthy'
                        : 'unhealthy'
                    }`
                  : 'Backup health unavailable'}
              </small>
            </article>
          )}
        </section>
      )}

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

        {canReadAgents && (
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
        )}

        {canReadAgents && (
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
        )}

        {canReadWorkspace && (
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
        )}

        {canReadWorkspace && (
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
        )}
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

        {canReadAgents && (
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
        )}

        {canReadAgents && (
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
        )}

        {canReadWorkspace && (
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
        )}

        {canReadWorkspace && (
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
        )}

        {canReadActions && (
          <article className="panel">
            <div className="panel__title">
              <ShieldCheck size={20} />
              <h2>Action queue</h2>
            </div>

            {actions.isLoading && (
              <div className="placeholder">
                Loading action plans…
              </div>
            )}

            {actions.isError && (
              <div className="placeholder">
                Action queue unavailable.
              </div>
            )}

            {actions.isSuccess
              && actionPlans.length === 0
              && (
                <div className="placeholder">
                  No action plans.
                </div>
              )}

            {actions.isSuccess
              && actionPlans.length > 0
              && (
                <>
                  <div className="readiness-row">
                    <span>Awaiting approval</span>
                    <strong>{awaitingApproval}</strong>
                  </div>

                  <div className="readiness-row">
                    <span>Queued</span>
                    <strong>{queuedActions}</strong>
                  </div>

                  <div className="readiness-row">
                    <span>Executing</span>
                    <strong>{executingActions}</strong>
                  </div>

                  <div className="readiness-row">
                    <span>Verifying</span>
                    <strong>{verifyingActions}</strong>
                  </div>

                  <div className="readiness-row">
                    <span>Failed</span>
                    <strong>{failedActions}</strong>
                  </div>

                  <div className="readiness-row">
                    <span>Rejected</span>
                    <strong>{rejectedActions}</strong>
                  </div>

                  {actionPlans
                    .slice(0, 4)
                    .map((plan) => (
                      <div
                        className="readiness-row"
                        key={plan.id}
                      >
                        <span>{plan.capability}</span>
                        <strong>
                          {plan.status.toUpperCase()}
                        </strong>
                      </div>
                    ))}

                  <div className="readiness-row">
                    <span>Policy queue</span>
                    <Link to="/actions">
                      Open actions
                    </Link>
                  </div>
                </>
              )}
          </article>
        )}

        {canReadAudit && (
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
        )}

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
