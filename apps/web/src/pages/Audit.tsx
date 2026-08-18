import {
  ClipboardList,
  Fingerprint,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import {
  getAuditEvents,
  type AuditEvent,
} from '../api/audit'
import { useAuth } from '../auth/useAuth'

function formatResult(
  result: unknown,
) {
  if (result === null
    || result === undefined) {
    return '—'
  }

  if (typeof result === 'string') {
    return result
  }

  try {
    return JSON.stringify(result)
  } catch {
    return String(result)
  }
}

function shortHash(
  value: string | null,
) {
  if (!value) {
    return '—'
  }

  return value.length > 16
    ? `${value.slice(0, 16)}…`
    : value
}

function AuditRow({
  event,
}: {
  event: AuditEvent
}) {
  return (
    <article className="ops-row">
      <div className="ops-row__main">
        <div className="ops-row__heading">
          <ClipboardList size={16} />

          <strong>
            {event.action}
          </strong>

          <span className="status-badge">
            {event.target_type ?? 'event'}
          </span>
        </div>

        <small>
          {new Date(
            event.created_at,
          ).toLocaleString()}
          {' · actor '}
          {event.actor_id ?? 'system'}
        </small>

        <div className="audit-result">
          {formatResult(event.result)}
        </div>
      </div>

      <div className="audit-chain">
        <Fingerprint size={14} />

        <code title={event.hash}>
          {shortHash(event.hash)}
        </code>

        <span>←</span>

        <code title={
          event.previous_hash ?? ''
        }>
          {shortHash(
            event.previous_hash,
          )}
        </code>
      </div>
    </article>
  )
}

export function Audit() {
  const auth = useAuth()
  const token = auth.tokens?.access_token
  const workspaceId = auth.workspace?.id

  const events = useQuery({
    queryKey: [
      'audit',
      workspaceId,
    ],
    queryFn: () =>
      getAuditEvents(
        token!,
        workspaceId!,
        100,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Immutable operations history
          </p>
          <h1>Audit</h1>
          <p>
            Workspace-scoped security and
            operational events.
          </p>
        </div>

        <div className="system-pill">
          <Fingerprint size={16} />
          HASH CHAIN
        </div>
      </header>

      {events.isError && (
        <div className="auth-error">
          Failed to load audit events.
        </div>
      )}

      <section className="panel ops-panel">
        <div className="ops-title">
          <ClipboardList size={18} />
          <div>
            <strong>
              Recent audit events
            </strong>
            <small>
              Latest 100 events
            </small>
          </div>
        </div>

        {events.isLoading && (
          <div className="ops-empty">
            Loading audit log…
          </div>
        )}

        {events.data?.length === 0 && (
          <div className="ops-empty">
            No audit events.
          </div>
        )}

        <div className="ops-list">
          {events.data?.map(
            (event) => (
              <AuditRow
                key={event.id}
                event={event}
              />
            ),
          )}
        </div>
      </section>
    </>
  )
}
