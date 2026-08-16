# AI-project SRV v0.1.25-alpha

## Production Observability

v0.1.25-alpha introduces production-oriented Prometheus telemetry for the API,
notification delivery subsystem, and independent background workers.

## Prometheus endpoint

New endpoint:

`GET /metrics`

The endpoint uses Prometheus exposition format and is excluded from OpenAPI.

It is also excluded from its own HTTP request instrumentation.

## HTTP observability

New metrics include:

- `srv_http_requests_total`;
- `srv_http_request_duration_seconds`.

Labels are intentionally low-cardinality:

- HTTP method;
- FastAPI route template;
- status code.

Concrete IDs are never used as route labels.

Unknown paths are represented as:

`__unmatched__`

## Notification delivery observability

Persisted notification delivery state is exported for both:

- backup alert delivery;
- agent lifecycle alert delivery.

Metrics cover:

- pending;
- sending;
- delivered;
- failed;
- canceled;
- retryable failures;
- exhausted failures;
- stale sending deliveries;
- oldest pending age.

Collection status is exposed by:

`srv_notification_metrics_collection_success`

No workspace IDs, delivery IDs, alert IDs, destination IDs, or endpoints are
used as metric labels.

## Worker operational state

Alembic migration:

`0021_worker_operational_state`

adds:

`worker_operational_states`

for:

- `backup_scheduler`;
- `backup_alert_delivery`;
- `agent_lifecycle_alert_delivery`.

Worker loops persist:

- iteration start;
- completion;
- success;
- failure;
- heartbeat;
- processed item count;
- bounded error state.

Observability persistence failures are fail-open and do not stop the worker
loop.

## Worker Prometheus metrics

New worker metrics include:

- `srv_worker_state_present`;
- `srv_worker_heartbeat_fresh`;
- `srv_worker_heartbeat_stale_after_seconds`;
- `srv_worker_last_heartbeat_age_seconds`;
- `srv_worker_last_success_age_seconds`;
- `srv_worker_last_processed_count`;
- `srv_worker_last_iteration_success`;
- `srv_worker_metrics_collection_success`.

Worker labels are restricted to three fixed worker names.

## Runtime validation

Runtime validation confirmed that all three workers persist operational state in
PostgreSQL and are visible through `/metrics`.

Healthy runtime samples showed:

- all three worker-state rows present;
- successful iteration state;
- fresh heartbeats;
- worker metric collection success;
- notification metric collection success.

## Database validation

Migration chain:

`0020_delivery_cursor_indexes -> 0021_worker_operational_state`

The resulting PostgreSQL table includes:

- primary key on `worker_name`;
- check constraint restricting supported workers;
- timezone-aware operational timestamps;
- default processed count of zero;
- default update timestamp.

## Readiness

`/ready` is unchanged.

Infrastructure readiness remains based only on:

- PostgreSQL;
- Redis.

Worker or notification delivery degradation does not change readiness.

## Operational boundaries

This release does not:

- restart workers;
- retry deliveries from metrics;
- mutate notification routing;
- perform automatic remediation.

Metrics are observational signals only.

**LLM advisory, Policy Engine authoritative.**

## Validation

Development validation includes:

- HTTP metric route normalization tests;
- unmatched-route cardinality tests;
- `/metrics` self-instrumentation exclusion;
- notification delivery aggregation tests;
- notification problem classification tests;
- oldest pending age tests;
- collection failure isolation tests;
- persistent worker-state service tests;
- worker success/failure instrumentation tests;
- fail-open observability persistence tests;
- worker heartbeat freshness tests;
- missing-worker metric semantics;
- Prometheus bounded-label tests;
- PostgreSQL schema inspection;
- live worker persistence validation;
- live `/metrics` validation;
- full API regression;
- Python compilation;
- `git diff --check`.

Latest validated full API result:

`262 passed, 1 known warning`

Known warning:

Starlette TestClient reports the existing httpx deprecation warning.

Current Alembic head:

`0021_worker_operational_state`
