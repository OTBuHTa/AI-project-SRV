# ADR-028: Notification Delivery Query Scalability

## Status

Accepted for v0.1.23-alpha.

## Context

v0.1.22-alpha introduced unified read-only notification delivery
observability across backup and agent lifecycle delivery pipelines.

The initial API supported bounded listing and basic filtering, but clients
could not efficiently navigate larger delivery histories or determine total
result counts.

The underlying backup and agent lifecycle delivery tables remain separate.

## Decision

Extend notification delivery observability with scalable read-only query
capabilities.

### Delivery history

`GET /api/v1/notifications/deliveries`

Supports:

- source;
- status;
- destination ID;
- channel;
- creation time range;
- offset;
- bounded limit.

Pagination is global across backup and agent lifecycle sources.

Each source query loads only the required `offset + limit` window. Results are
then merged, globally ordered newest first, and the requested page is sliced
after the merge.

Applying SQL OFFSET independently to each source is intentionally avoided
because it would produce incorrect global pagination.

### Problem delivery view

`GET /api/v1/notifications/deliveries/problems`

Supports:

- source;
- problem classification;
- destination ID;
- channel;
- creation time range;
- offset;
- bounded limit.

Problem classifications remain:

- `retryable_failed`;
- `exhausted_failed`;
- `stale_sending`.

The same global merge and pagination semantics apply.

### Delivery counts

Expose:

`GET /api/v1/notifications/deliveries/count`

and:

`GET /api/v1/notifications/deliveries/problems/count`

Count responses contain:

- total;
- backup;
- agent lifecycle.

Count queries use the same workspace and filtering semantics as their
corresponding list endpoints.

Problem counts include only deliveries matching operational problem
conditions. An omitted problem filter means all supported problem
classifications, not all deliveries.

### Authorization

All endpoints require:

`workspace.read`

All queries are scoped to the authenticated workspace.

### Operational boundaries

This release remains read-only.

It does not:

- retry deliveries;
- cancel deliveries;
- modify delivery state;
- modify destinations;
- modify notification routing;
- invoke workers;
- perform automatic remediation.

Delivery observability does not alter `/ready`.

`/ready` remains infrastructure readiness for DB and Redis.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- large delivery histories can be paginated predictably;
- filtering can be performed server-side;
- problem queues can be filtered by operational classification;
- clients can obtain result totals without loading delivery records;
- source-specific SQL queries remain isolated;
- existing delivery persistence and worker semantics remain unchanged.

### Tradeoffs

- global offset pagination requires each selected source to expose an
  `offset + limit` candidate window;
- large offsets remain more expensive than cursor-based pagination;
- aggregate count requests query each selected persistence source;
- backup and lifecycle persistence remain intentionally separate.

## Database

No database migration is introduced.

Alembic head remains:

`0019_agent_lifecycle_deliveries`
