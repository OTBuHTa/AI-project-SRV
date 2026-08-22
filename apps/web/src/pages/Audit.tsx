import {
  ClipboardList,
  Fingerprint,
  Search,
} from 'lucide-react'
import {
  useMemo,
  useState,
} from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  getAuditEvents,
  type AuditEvent,
} from '../api/audit'
import { useAuth } from '../auth/useAuth'

function formatResult(
  result: unknown,
) {
  if (
    result === null
    || result === undefined
  ) {
    return '—'
  }

  if (typeof result === 'string') {
    return result
  }

  try {
    return JSON.stringify(
      result,
      null,
      2,
    )
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

function includesValue(
  value: string | null,
  query: string,
) {
  return (
    value
      ?.toLowerCase()
      .includes(query)
    ?? false
  )
}

function matchesAuditSearch(
  event: AuditEvent,
  rawQuery: string,
) {
  const query =
    rawQuery.trim().toLowerCase()

  if (!query) {
    return true
  }

  return (
    event.action
      .toLowerCase()
      .includes(query)
    || includesValue(
      event.actor_id,
      query,
    )
    || includesValue(
      event.target_type,
      query,
    )
    || includesValue(
      event.target_id,
      query,
    )
    || includesValue(
      event.request_id,
      query,
    )
    || event.hash
      .toLowerCase()
      .includes(query)
    || includesValue(
      event.previous_hash,
      query,
    )
    || formatResult(event.result)
      .toLowerCase()
      .includes(query)
  )
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

        <div className="ops-details">
          <div>
            <span>Target</span>
            <code>
              {event.target_id ?? '—'}
            </code>
          </div>

          <div>
            <span>Request</span>
            <code>
              {event.request_id ?? '—'}
            </code>
          </div>

          <div>
            <span>Event ID</span>
            <code>
              {event.id}
            </code>
          </div>
        </div>

        <div className="action-parameters">
          <span>Result</span>
          <code>
            {formatResult(event.result)}
          </code>
        </div>
      </div>

      <div className="audit-chain">
        <Fingerprint size={14} />

        <code title={event.hash}>
          {shortHash(event.hash)}
        </code>

        <span>←</span>

        <code
          title={
            event.previous_hash ?? ''
          }
        >
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

  const token =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

  const [
    limit,
    setLimit,
  ] = useState<100 | 250 | 500>(100)

  const [
    search,
    setSearch,
  ] = useState('')

  const events = useQuery({
    queryKey: [
      'audit',
      workspaceId,
      limit,
    ],
    queryFn: () =>
      getAuditEvents(
        token!,
        workspaceId!,
        limit,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  const filteredEvents =
    useMemo(
      () =>
        (events.data ?? []).filter(
          (event) =>
            matchesAuditSearch(
              event,
              search,
            ),
        ),
      [
        events.data,
        search,
      ],
    )

  const actorCount =
    new Set(
      (events.data ?? [])
        .map(
          (event) =>
            event.actor_id
            ?? 'system',
        ),
    ).size

  const actionCount =
    new Set(
      (events.data ?? [])
        .map(
          (event) =>
            event.action,
        ),
    ).size

  const requestCount =
    (events.data ?? [])
      .filter(
        (event) =>
          Boolean(event.request_id),
      )
      .length

  const linkedCount =
    (events.data ?? [])
      .filter(
        (event) =>
          Boolean(event.previous_hash),
      )
      .length

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
            operational events with stored
            hash-chain metadata.
          </p>
        </div>

        <div className="system-pill">
          <Fingerprint size={16} />
          CHAIN METADATA
        </div>
      </header>

      <section className="ops-stat-grid">
        <article className="ops-stat">
          <span>Loaded events</span>
          <strong>
            {events.data?.length ?? 0}
          </strong>
          <small>
            Latest workspace events
          </small>
        </article>

        <article className="ops-stat">
          <span>Actions</span>
          <strong>
            {actionCount}
          </strong>
          <small>
            Distinct action names
          </small>
        </article>

        <article className="ops-stat">
          <span>Actors</span>
          <strong>
            {actorCount}
          </strong>
          <small>
            Distinct actor IDs
          </small>
        </article>

        <article className="ops-stat">
          <span>Previous hash present</span>
          <strong>
            {linkedCount}
          </strong>
          <small>
            Metadata only, not verification
          </small>
        </article>
      </section>

      <section className="panel ops-panel">
        <div className="ops-title">
          <Search size={18} />

          <div>
            <strong>
              Audit view
            </strong>

            <small>
              Search is local to the loaded
              event window
            </small>
          </div>
        </div>

        <div className="notification-filter-grid">
          <label>
            <span>Search loaded events</span>

            <input
              type="search"
              value={search}
              placeholder={
                'Action, actor, target, '
                + 'request or hash'
              }
              onChange={(event) =>
                setSearch(
                  event.target.value,
                )
              }
            />
          </label>

          <label>
            <span>Load limit</span>

            <select
              value={limit}
              onChange={(event) =>
                setLimit(
                  Number(
                    event.target.value,
                  ) as 100 | 250 | 500,
                )
              }
            >
              <option value={100}>
                100
              </option>

              <option value={250}>
                250
              </option>

              <option value={500}>
                500
              </option>
            </select>
          </label>
        </div>

        <div className="ops-details">
          <div>
            <span>Visible</span>
            <strong>
              {filteredEvents.length}
            </strong>
          </div>

          <div>
            <span>Request IDs</span>
            <strong>
              {requestCount}
            </strong>
          </div>

          <div>
            <span>Server ordering</span>
            <strong>
              Newest first
            </strong>
          </div>

          <div>
            <span>Integrity verification</span>
            <strong>
              Not exposed by API
            </strong>
          </div>
        </div>
      </section>

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
              Server limit {limit}
              {' · '}
              {filteredEvents.length}
              {' visible'}
            </small>
          </div>
        </div>

        {events.isLoading && (
          <div className="ops-empty">
            Loading audit log…
          </div>
        )}

        {events.isSuccess
          && filteredEvents.length === 0
          && (
            <div className="ops-empty">
              No audit events match
              the current view.
            </div>
          )}

        <div className="ops-list">
          {filteredEvents.map(
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
