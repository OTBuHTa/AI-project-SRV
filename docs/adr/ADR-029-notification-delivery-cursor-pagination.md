# ADR-029: Notification Delivery Cursor Pagination

## Status

Accepted for v0.1.24-alpha.

## Context

v0.1.23-alpha introduced globally correct offset pagination across backup and
agent-lifecycle notification delivery persistence.

Offset pagination is API-compatible and correct, but its database cost grows
with page depth because each selected source must load an `offset + limit`
candidate window.

Notification delivery observability also spans independent persistence tables,
so cursor pagination requires a deterministic global ordering.

Problem delivery pagination has an additional time-dependent property:
`stale_sending` classification changes as observation time advances.

## Decision

Introduce cursor-based keyset pagination as additional read-only APIs while
retaining existing offset APIs for compatibility.

## API

Expose:

`GET /api/v1/notifications/deliveries/page`

and:

`GET /api/v1/notifications/deliveries/problems/page`

Each response contains:

- `items`;
- `next_cursor`;
- `has_more`;
- `observed_at`.

## Ordering

The global descending ordering key is:

`(created_at, source, id)`

This produces deterministic cross-source ordering even when records from
different delivery tables share the same timestamp.

## Keyset access

Each selected source applies a cursor boundary predicate before loading
records.

Queries use:

`LIMIT limit + 1`

and do not use SQL OFFSET.

The extra record determines whether another page exists.

## Observation semantics

The first page establishes `observed_at`.

That value is carried through subsequent cursors.

History pagination restricts records to:

`created_at <= observed_at`

This prevents newly created deliveries from appearing midway through a cursor
traversal.

Problem pagination additionally uses the preserved observation timestamp for
the `stale_sending` timeout calculation.

This stabilizes time-based classification between pages.

The observation boundary is not a database transaction snapshot. Existing rows
may still be changed by delivery workers between requests.

## Cursor structure

The opaque cursor contains:

- cursor format version;
- endpoint scope;
- created timestamp;
- source;
- record ID;
- filter fingerprint;
- observation timestamp.

The filter fingerprint includes the workspace and active query filters.

A cursor cannot be reused with another workspace, endpoint scope, or filter
set.

The cursor is encoded but is not an authorization mechanism.

Authorization remains enforced by `workspace.read` and workspace-scoped
database queries.

## Invalid cursors

Malformed, unsupported, scope-mismatched, or filter-mismatched cursors are
rejected.

The public API returns:

`400 invalid_notification_delivery_cursor`

Internal parsing details are not returned to clients.

## Database indexes

Migration:

`0020_delivery_cursor_indexes`

adds:

`(workspace_id, created_at, id)`

indexes to:

- `backup_alert_deliveries`;
- `agent_lifecycle_alert_deliveries`.

These indexes support workspace-scoped descending keyset access.

PostgreSQL query-plan validation confirmed index-only scans for both delivery
sources.

## Backward compatibility

Existing offset APIs remain supported.

Clients can migrate to cursor pagination without an immediate breaking change.

## Authorization and isolation

Cursor APIs require:

`workspace.read`

Every source query remains constrained by the active workspace.

Persistence sources remain isolated and are merged only at the observability
service layer.

## Operational boundaries

Cursor pagination is observational only.

It does not:

- mutate deliveries;
- retry deliveries;
- cancel deliveries;
- change routing;
- invoke delivery workers;
- execute infrastructure actions;
- perform automatic remediation.

Notification delivery state does not alter `/ready`.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- pagination cost no longer grows directly with offset depth;
- page boundaries are deterministic across persistence sources;
- newly created rows do not enter an active history traversal;
- stale-sending time evaluation remains stable across pages;
- existing clients retain the offset API;
- keyset queries have dedicated composite indexes.

### Tradeoffs

- cursors carry query state;
- clients cannot directly jump to arbitrary page numbers;
- changing filters invalidates a cursor;
- offset and cursor APIs must coexist during the compatibility period;
- observation semantics are not equivalent to an immutable transaction
  snapshot.

## Database

Alembic head:

`0020_delivery_cursor_indexes`
