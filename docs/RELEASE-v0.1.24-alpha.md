# AI-project SRV v0.1.24-alpha

## Notification Delivery Cursor Pagination

v0.1.24-alpha adds scalable cursor-based pagination for unified notification
delivery observability.

Existing offset-based APIs remain available for backward compatibility.

## New cursor endpoints

### Delivery history

`GET /api/v1/notifications/deliveries/page`

Supports:

- source;
- status;
- destination ID;
- channel;
- timezone-aware created-from / created-to range;
- opaque cursor;
- bounded limit.

Response contains:

- `items`;
- `next_cursor`;
- `has_more`;
- `observed_at`.

### Delivery problems

`GET /api/v1/notifications/deliveries/problems/page`

Supports:

- source;
- problem classification;
- destination ID;
- channel;
- timezone-aware created-from / created-to range;
- opaque cursor;
- bounded limit.

Problem classifications remain:

- `retryable_failed`;
- `exhausted_failed`;
- `stale_sending`.

## Keyset pagination

Cursor endpoints use keyset pagination instead of SQL OFFSET.

Each persistence source loads only a bounded candidate window using:

`LIMIT limit + 1`

The extra candidate determines whether another page exists.

## Stable global ordering

Unified ordering across backup and agent-lifecycle delivery sources is:

`(created_at, source, id)`

descending.

The source component makes page boundaries deterministic when independent
persistence tables contain deliveries with the same timestamp.

## Observation snapshot

The first page captures `observed_at`.

Subsequent cursors preserve that observation timestamp.

History queries exclude deliveries created after the observation boundary.

Problem pagination also preserves the observation time used for
`stale_sending` classification.

This provides stable time-based pagination semantics without claiming a full
database MVCC snapshot.

## Cursor validation

Cursors contain:

- format version;
- endpoint scope;
- page boundary timestamp;
- source;
- delivery ID;
- query filter fingerprint;
- observation timestamp.

Cursors are opaque API values.

Malformed, unsupported, scope-mismatched, and filter-mismatched cursors return:

`400 invalid_notification_delivery_cursor`

Workspace identity is included in the filter fingerprint, so cursors cannot be
reused across workspaces.

Authorization remains enforced independently by `workspace.read` and
workspace-scoped persistence queries.

## Database scalability

Alembic migration:

`0020_delivery_cursor_indexes`

adds composite indexes:

`(workspace_id, created_at, id)`

to:

- `backup_alert_deliveries`;
- `agent_lifecycle_alert_deliveries`.

PostgreSQL query-plan validation confirmed `Index Only Scan Backward` for both
workspace-scoped ordered queries.

The migration was verified in both directions:

`0019 -> 0020 -> 0019 -> 0020`

## Backward compatibility

Existing APIs remain unchanged:

- `GET /api/v1/notifications/deliveries`
- `GET /api/v1/notifications/deliveries/problems`
- `GET /api/v1/notifications/deliveries/count`
- `GET /api/v1/notifications/deliveries/problems/count`
- `GET /api/v1/notifications/deliveries/health`

Offset pagination is not removed in this release.

## Operational boundaries

Cursor APIs are read-only.

This release does not:

- retry deliveries;
- cancel deliveries;
- mutate delivery state;
- change notification routing;
- invoke delivery workers;
- perform automatic remediation.

Notification delivery degradation does not change `/ready`.

`/ready` remains infrastructure readiness for DB and Redis.

**LLM advisory, Policy Engine authoritative.**

## Validation

Development validation includes:

- cursor encode/decode tests;
- filter fingerprint mismatch tests;
- cross-workspace cursor rejection;
- stable global ordering tests;
- same-timestamp cross-source boundary tests;
- no-repeat page-boundary tests;
- history observation snapshot tests;
- problem observation snapshot tests;
- API error mapping tests;
- OpenAPI endpoint validation;
- Alembic upgrade/downgrade validation;
- PostgreSQL composite-index inspection;
- PostgreSQL query-plan validation;
- focused notification regression;
- full API regression;
- Python compilation;
- `git diff --check`.

Latest validated test results:

- focused notification suite: `68 passed`;
- full API suite: `233 passed, 1 known warning`.

Known warning:

Starlette TestClient reports the existing httpx deprecation warning.

Current Alembic head:

`0020_delivery_cursor_indexes`
