import {
  Archive,
  CheckCircle2,
  Clock3,
  Database,
  Play,
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  createBackup,
  getActiveBackupAlertEvents,
  getBackupAlertEvents,
  getBackupHealth,
  getBackupJobs,
  getBackupProtection,
  getBackupSchedule,
  getBackupStatus,
  getBackupStorageHealth,
} from '../api/backups'
import { useAuth } from '../auth/useAuth'

function formatDate(
  value: string | null | undefined,
) {
  if (!value) {
    return '—'
  }

  return new Date(value).toLocaleString()
}

function duration(
  seconds: number | null | undefined,
) {
  if (seconds === null
    || seconds === undefined) {
    return '—'
  }

  if (seconds < 60) {
    return `${seconds}s`
  }

  if (seconds < 3600) {
    return `${Math.round(seconds / 60)}m`
  }

  return `${(
    seconds / 3600
  ).toFixed(1)}h`
}

export function Backups() {
  const auth = useAuth()
  const token = auth.tokens?.access_token
  const workspaceId = auth.workspace?.id
  const queryClient = useQueryClient()

  const overview = useQuery({
    queryKey: [
      'backups',
      workspaceId,
    ],
    queryFn: async () => {
      const [
        jobs,
        status,
        health,
        storage,
        schedule,
        protection,
        activeAlerts,
        alertHistory,
      ] = await Promise.all([
        getBackupJobs(token!, workspaceId!),
        getBackupStatus(token!, workspaceId!),
        getBackupHealth(token!, workspaceId!),
        getBackupStorageHealth(token!, workspaceId!),
        getBackupSchedule(token!, workspaceId!),
        getBackupProtection(token!, workspaceId!),
        getActiveBackupAlertEvents(
          token!,
          workspaceId!,
        ),
        getBackupAlertEvents(
          token!,
          workspaceId!,
        ),
      ])

      return {
        jobs,
        status,
        health,
        storage,
        schedule,
        protection,
        activeAlerts,
        alertHistory,
      }
    },
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  const runBackup = useMutation({
    mutationFn: () =>
      createBackup(
        token!,
        workspaceId!,
        'full',
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['backups'],
      })
    },
  })

  const data = overview.data

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Recovery and protection
          </p>
          <h1>Backups</h1>
          <p>
            Backup health, scheduler,
            storage and execution history.
          </p>
        </div>

        <button
          type="button"
          className="primary-button"
          disabled={
            !token
            || !workspaceId
            || runBackup.isPending
          }
          onClick={() =>
            runBackup.mutate()
          }
        >
          <Play size={16} />
          {runBackup.isPending
            ? 'Running…'
            : 'Run full backup'}
        </button>
      </header>

      {overview.isError && (
        <div className="auth-error">
          Failed to load backup state.
        </div>
      )}

      {runBackup.isError && (
        <div className="auth-error">
          Backup execution failed.
        </div>
      )}

      {runBackup.isSuccess && (
        <div className="ops-success">
          Backup job completed with status:
          {' '}
          {runBackup.data.status}
        </div>
      )}

      <section className="ops-stat-grid">
        <article className="ops-stat">
          <span>Protection</span>
          <strong>
            {data?.status.status ?? '—'}
          </strong>
          <small>
            {data?.status.reason
              ?? 'Loading…'}
          </small>
        </article>

        <article className="ops-stat">
          <span>Verification</span>
          <strong>
            {data?.health.status ?? '—'}
          </strong>
          <small>
            {data
              ? `${data.health.verified_count} verified`
              : 'Loading…'}
          </small>
        </article>

        <article className="ops-stat">
          <span>Storage</span>
          <strong>
            {data
              ? (
                  data.storage.healthy
                    ? 'healthy'
                    : 'degraded'
                )
              : '—'}
          </strong>
          <small>
            {data?.storage.backend ?? '—'}
          </small>
        </article>

        <article className="ops-stat">
          <span>Failed jobs</span>
          <strong>
            {data?.status.failed_jobs
              ?? '—'}
          </strong>
          <small>
            Scheduler lag{' '}
            {duration(
              data?.status
                .scheduler_lag_seconds,
            )}
          </small>
        </article>
      </section>

      <section className="ops-grid">
        <article className="panel ops-panel">
          <div className="ops-title">
            <ShieldCheck size={18} />
            <strong>Protection summary</strong>
          </div>

          <div className="ops-details">
            <div>
              <span>Protected</span>
              <strong>
                {data
                  ? (
                      data.protection.protected
                        ? 'yes'
                        : 'no'
                    )
                  : '—'}
              </strong>
            </div>

            <div>
              <span>Status</span>
              <strong>
                {data?.protection.status ?? '—'}
              </strong>
            </div>

            <div>
              <span>Last verified</span>
              <strong>
                {formatDate(
                  data?.protection
                    .last_verified_at,
                )}
              </strong>
            </div>

            <div>
              <span>Protection alerts</span>
              <strong>
                {data?.protection.alerts.length
                  ?? '—'}
              </strong>
            </div>
          </div>

          {data?.protection.reason && (
            <div className="ops-empty">
              {data.protection.reason}
            </div>
          )}
        </article>

        <article className="panel ops-panel">
          <div className="ops-title">
            <TriangleAlert size={18} />
            <strong>Active backup alerts</strong>
          </div>

          {!data && (
            <div className="ops-empty">
              Loading active alerts…
            </div>
          )}

          {data
            && data.activeAlerts.length === 0
            && (
              <div className="ops-empty">
                No active backup alerts.
              </div>
            )}

          <div className="ops-list">
            {data?.activeAlerts.map(
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
                      last seen{' '}
                      {formatDate(
                        alert.last_seen_at,
                      )}
                      {' · '}
                      {alert.acknowledged_at
                        ? 'acknowledged'
                        : 'unacknowledged'}
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
            <strong>Backup alert history</strong>
            <small>
              Latest workspace alert events
            </small>
          </div>
        </div>

        {!data && (
          <div className="ops-empty">
            Loading alert history…
          </div>
        )}

        {data
          && data.alertHistory.length === 0
          && (
            <div className="ops-empty">
              No backup alert events recorded.
            </div>
          )}

        <div className="ops-list">
          {data?.alertHistory.map(
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
                    {formatDate(
                      alert.first_seen_at,
                    )}
                    {' · last seen '}
                    {formatDate(
                      alert.last_seen_at,
                    )}
                  </small>
                </div>

                <span>
                  {alert.message}
                </span>

                <small>
                  resolved{' '}
                  {formatDate(
                    alert.resolved_at,
                  )}
                  {' · acknowledged '}
                  {formatDate(
                    alert.acknowledged_at,
                  )}
                  {' · by '}
                  {alert.acknowledged_by ?? '—'}
                </small>
              </article>
            ),
          )}
        </div>
      </section>

      <section className="ops-grid">
        <article className="panel ops-panel">
          <div className="ops-title">
            <Clock3 size={18} />
            <strong>Schedule</strong>
          </div>

          {data?.schedule ? (
            <div className="ops-details">
              <div>
                <span>Status</span>
                <strong>
                  {data.schedule.enabled
                    ? 'enabled'
                    : 'disabled'}
                </strong>
              </div>

              <div>
                <span>Interval</span>
                <strong>
                  {data.schedule
                    .interval_minutes} min
                </strong>
              </div>

              <div>
                <span>Next run</span>
                <strong>
                  {formatDate(
                    data.schedule
                      .next_run_at,
                  )}
                </strong>
              </div>

              <div>
                <span>Retention</span>
                <strong>
                  {data.schedule
                    .retention_keep_last}
                  {' backups / '}
                  {data.schedule
                    .retention_max_age_days}
                  d
                </strong>
              </div>
            </div>
          ) : (
            <div className="ops-empty">
              No backup schedule configured.
            </div>
          )}
        </article>

        <article className="panel ops-panel">
          <div className="ops-title">
            <Database size={18} />
            <strong>Storage</strong>
          </div>

          <div className="ops-details">
            <div>
              <span>Backend</span>
              <strong>
                {data?.storage.backend
                  ?? '—'}
              </strong>
            </div>

            <div>
              <span>Readable</span>
              <strong>
                {data
                  ? String(
                      data.storage.readable,
                    )
                  : '—'}
              </strong>
            </div>

            <div>
              <span>Writable</span>
              <strong>
                {data
                  ? String(
                      data.storage.writable,
                    )
                  : '—'}
              </strong>
            </div>

            <div>
              <span>Root</span>
              <code>
                {data?.storage.root ?? '—'}
              </code>
            </div>
          </div>
        </article>
      </section>

      <section className="panel ops-panel">
        <div className="ops-title">
          <Archive size={18} />
          <div>
            <strong>
              Backup jobs
            </strong>
            <small>
              Workspace execution history
            </small>
          </div>
        </div>

        {overview.isLoading && (
          <div className="ops-empty">
            Loading backup state…
          </div>
        )}

        {data?.jobs.length === 0 && (
          <div className="ops-empty">
            No backup jobs yet.
          </div>
        )}

        <div className="ops-list">
          {data?.jobs.map((job) => (
            <article
              className="ops-row"
              key={job.id}
            >
              <div className="ops-row__main">
                <div className="ops-row__heading">
                  {job.status
                    === 'completed'
                    || job.status
                      === 'succeeded'
                    ? (
                        <CheckCircle2
                          size={16}
                        />
                      )
                    : (
                        <Clock3 size={16} />
                      )}

                  <strong>
                    {job.backup_type}
                  </strong>

                  <span
                    className={
                      job.status
                        === 'completed'
                      || job.status
                        === 'succeeded'
                        ? (
                            'status-badge '
                            + 'status-badge--ok'
                          )
                        : 'status-badge'
                    }
                  >
                    {job.status}
                  </span>
                </div>

                <small>
                  created{' '}
                  {formatDate(
                    job.created_at,
                  )}
                  {' · completed '}
                  {formatDate(
                    job.completed_at,
                  )}
                </small>
              </div>

              {job.error && (
                <code className="ops-error">
                  {job.error}
                </code>
              )}
            </article>
          ))}
        </div>
      </section>
    </>
  )
}
