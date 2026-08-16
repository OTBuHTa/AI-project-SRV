# ADR-030: Production Observability

## Status

Accepted for v0.1.25-alpha.

## Context

AI-project SRV already exposes infrastructure readiness through `/ready` and
domain-specific notification delivery observability through authenticated APIs.

Production operation also requires low-cardinality machine-readable metrics for:

- API request volume and latency;
- HTTP status outcomes;
- persisted notification delivery state;
- notification delivery degradation;
- delivery queue age;
- background worker heartbeat and iteration state.

Background workers run as independent processes, so process-local counters in
the API cannot accurately represent their runtime state.

Operational degradation must remain distinct from infrastructure readiness.

## Decision

Expose a Prometheus-compatible `/metrics` endpoint and persist operational state
for independent background workers in PostgreSQL.

## HTTP metrics

The API exports:

- `srv_http_requests_total`;
- `srv_http_request_duration_seconds`.

HTTP labels are bounded to:

- method;
- route template;
- status code.

Matched dynamic routes use their FastAPI route template rather than concrete
resource identifiers.

Unmatched routes use the fixed label:

`__unmatched__`

The `/metrics` endpoint does not instrument itself.

## Notification delivery metrics

The API derives notification delivery metrics from persisted database state.

Metrics include:

- current deliveries by source and status;
- retryable failures;
- exhausted failures;
- stale sending deliveries;
- oldest pending delivery age.

Sources are limited to:

- `backup`;
- `agent_lifecycle`.

No workspace IDs, delivery IDs, destination IDs, endpoints, or other
high-cardinality identifiers are exported as Prometheus labels.

Notification metrics collection failures are exposed through:

`srv_notification_metrics_collection_success`

Failed collection clears affected gauges rather than presenting stale data as
current state.

## Worker operational state

Migration:

`0021_worker_operational_state`

introduces:

`worker_operational_states`

One persistent row exists per known worker.

Supported worker names are constrained to:

- `backup_scheduler`;
- `backup_alert_delivery`;
- `agent_lifecycle_alert_delivery`.

Persisted state includes:

- last iteration start;
- last completion;
- last successful completion;
- last failure;
- last heartbeat;
- last iteration success status;
- last processed count;
- bounded last error;
- update timestamp.

Worker observability persistence is fail-open with respect to worker execution:
an observability write failure is logged but does not terminate the worker loop.

## Worker metrics

The API derives worker metrics from persisted operational state.

Metrics include:

- state presence;
- heartbeat freshness;
- heartbeat freshness threshold;
- heartbeat age;
- last successful iteration age;
- last processed count;
- last iteration success;
- collection success.

The worker label is limited to the fixed supported worker names.

Heartbeat freshness thresholds account for worker polling intervals:

- backup scheduler: 180 seconds;
- backup alert delivery: 90 seconds;
- agent lifecycle alert delivery: 90 seconds.

The signal is named heartbeat freshness rather than process `up`, because state
is persisted at iteration boundaries and does not claim continuous process
liveness.

## Failure isolation

Notification metrics collection and worker metrics collection are independent.

A failure collecting one subsystem does not invalidate successfully collected
metrics from the other subsystem.

`/metrics` remains available even when a domain metric collector cannot read
its operational state, with explicit collection-success gauges exposing the
failure.

## Readiness boundary

`/ready` remains infrastructure readiness only.

It continues to depend on:

- PostgreSQL;
- Redis.

Notification degradation, stale workers, failed workers, and delivery failures
do not make `/ready` fail.

## Operational boundaries

Observability is read-only from the operator perspective.

This release does not:

- retry failed notification deliveries;
- cancel deliveries;
- restart workers;
- execute infrastructure mutations;
- perform automatic remediation.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- Prometheus-compatible production telemetry;
- low-cardinality HTTP metrics;
- persisted cross-process worker observability;
- explicit queue and failure signals;
- observable collector failures;
- readiness remains semantically stable.

### Tradeoffs

- `/metrics` performs database-backed collection;
- worker heartbeat represents iteration-boundary persistence rather than
  continuous process liveness;
- persistent worker state requires an additional database table;
- current custom Prometheus registry does not expose default Python/process
  collectors;
- multi-process Prometheus aggregation is not required by the current
  single-process API deployment and would need separate handling if API worker
  count increases.

## Database

Alembic head:

`0021_worker_operational_state`
