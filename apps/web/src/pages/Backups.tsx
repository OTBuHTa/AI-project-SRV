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
  acknowledgeBackupAlert,
  createBackup,
  getActiveBackupAlertEvents,
  getBackupAlertEvents,
  getBackupAlerts,
  getBackupHealth,
  getBackupJobs,
  getBackupProtection,
  getBackupSchedule,
  getBackupStatus,
  getBackupStorageHealth,
  updateBackupSchedule,
  type BackupScheduleUpdate,
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
        alerts,
        activeAlerts,
        alertHistory,
      ] = await Promise.all([
        getBackupJobs(token!, workspaceId!),
        getBackupStatus(token!, workspaceId!),
        getBackupHealth(token!, workspaceId!),
        getBackupStorageHealth(token!, workspaceId!),
        getBackupSchedule(token!, workspaceId!),
        getBackupProtection(token!, workspaceId!),
        getBackupAlerts(token!, workspaceId!),
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
        alerts,
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

  const acknowledgeAlert = useMutation({
    mutationFn: (eventId: string) =>
      acknowledgeBackupAlert(
        token!,
        workspaceId!,
        eventId,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['backups'],
      })
    },
  })


  const updateSchedule = useMutation({
    mutationFn: (
      payload: BackupScheduleUpdate,
    ) =>
      updateBackupSchedule(
        token!,
        workspaceId!,
        payload,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [
          'backups',
          workspaceId,
        ],
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

      {acknowledgeAlert.isError && (
        <div className="auth-error">
          Backup alert acknowledgement failed.
        </div>
      )}

      {acknowledgeAlert.isSuccess && (
        <div className="ops-success">
          Backup alert acknowledged.
        </div>
      )}


      {updateSchedule.isError && (
        <div className="auth-error">
          Backup schedule update failed.
        </div>
      )}

      {updateSchedule.isSuccess && (
        <div className="ops-success">
          Backup schedule updated.
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

                  {!alert.acknowledged_at && (
                    <button
                      type="button"
                      className="sidebar-action"
                      disabled={
                        !token
                        || !workspaceId
                        || (
                          acknowledgeAlert.isPending
                          && acknowledgeAlert.variables
                            === alert.id
                        )
                      }
                      onClick={() =>
                        acknowledgeAlert.mutate(
                          alert.id,
                        )
                      }
                    >
                      <CheckCircle2 size={15} />
                      {acknowledgeAlert.isPending
                        && acknowledgeAlert.variables
                          === alert.id
                        ? 'Acknowledging…'
                        : 'Acknowledge'}
                    </button>
                  )}
                </article>
              ),
            )}
          </div>
        </article>
      </section>

      <section className="panel ops-panel">
        <div className="ops-title">
          <TriangleAlert size={18} />
          <div>
            <strong>
              Backup alert evaluation
            </strong>
            <small>
              Current evaluated backup alerts
            </small>
          </div>
        </div>

        {!data && (
          <div className="ops-empty">
            Loading backup alert evaluation…
          </div>
        )}

        {data && (
          <div className="ops-details">
            <div>
              <span>Status</span>
              <strong>
                {data.alerts.status}
              </strong>
            </div>

            <div>
              <span>Generated</span>
              <strong>
                {formatDate(
                  data.alerts.generated_at,
                )}
              </strong>
            </div>

            <div>
              <span>Alerts</span>
              <strong>
                {data.alerts.alerts.length}
              </strong>
            </div>
          </div>
        )}

        {data
          && data.alerts.alerts.length === 0
          && (
            <div className="ops-empty">
              No evaluated backup alerts.
            </div>
          )}

        <div className="ops-list">
          {data?.alerts.alerts.map(
            (alert) => (
              <article
                className="ops-row"
                key={`${alert.code}-${alert.severity}`}
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
                  </div>
                </div>

                <span>
                  {alert.message}
                </span>
              </article>
            ),
          )}
        </div>
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
            <div>
              <strong>Schedule</strong>
              <small>
                Manage automated backup policy.
              </small>
            </div>
          </div>

          {data?.schedule ? (
            <>
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

              <form
                key={[
                  data.schedule.enabled,
                  data.schedule.interval_minutes,
                  data.schedule.retention_keep_last,
                  data.schedule.retention_max_age_days,
                ].join(':')}
                onSubmit={(event) => {
                  event.preventDefault()

                  const form =
                    new FormData(
                      event.currentTarget,
                    )

                  const intervalMinutes =
                    Number(
                      form.get(
                        'interval_minutes',
                      ),
                    )

                  const retentionKeepLast =
                    Number(
                      form.get(
                        'retention_keep_last',
                      ),
                    )

                  const retentionMaxAgeDays =
                    Number(
                      form.get(
                        'retention_max_age_days',
                      ),
                    )

                  if (
                    !Number.isInteger(
                      intervalMinutes,
                    )
                    || !Number.isInteger(
                      retentionKeepLast,
                    )
                    || !Number.isInteger(
                      retentionMaxAgeDays,
                    )
                  ) {
                    return
                  }

                  updateSchedule.mutate({
                    enabled:
                      form.has('enabled'),
                    interval_minutes:
                      intervalMinutes,
                    retention_keep_last:
                      retentionKeepLast,
                    retention_max_age_days:
                      retentionMaxAgeDays,
                  })
                }}
              >
                <div className="notification-filter-grid">
                  <label className="field-label">
                    Enabled
                    <input
                      type="checkbox"
                      name="enabled"
                      defaultChecked={
                        data.schedule.enabled
                      }
                    />
                  </label>

                  <label className="field-label">
                    Interval minutes
                    <input
                      className="control-input"
                      type="number"
                      step="1"
                      name="interval_minutes"
                      defaultValue={
                        data.schedule
                          .interval_minutes
                      }
                      required
                    />
                  </label>

                  <label className="field-label">
                    Keep last
                    <input
                      className="control-input"
                      type="number"
                      step="1"
                      name="retention_keep_last"
                      defaultValue={
                        data.schedule
                          .retention_keep_last
                      }
                      required
                    />
                  </label>

                  <label className="field-label">
                    Max age days
                    <input
                      className="control-input"
                      type="number"
                      step="1"
                      name="retention_max_age_days"
                      defaultValue={
                        data.schedule
                          .retention_max_age_days
                      }
                      required
                    />
                  </label>
                </div>

                <div className="notification-filter-actions">
                  <button
                    type="submit"
                    className="sidebar-action"
                    disabled={
                      !token
                      || !workspaceId
                      || updateSchedule.isPending
                    }
                  >
                    {updateSchedule.isPending
                      ? 'Saving…'
                      : 'Save schedule'}
                  </button>
                </div>
              </form>
            </>
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
