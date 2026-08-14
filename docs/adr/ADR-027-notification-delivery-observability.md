# ADR-027: Notification Delivery Observability

## Status

Accepted for v0.1.22-alpha.

## Context

AI-project SRV already persists notification delivery state for backup alerts
and agent lifecycle alerts.

Both delivery pipelines expose operational state internally, including:

- pending;
- sending;
- delivered;
- failed;
- canceled;
- retry attempts;
- retry exhaustion;
- next-attempt timing;
- stale sending claims.

Before v0.1.22-alpha, operators did not have a unified read-only API for
observing those delivery pipelines.

The backup and agent lifecycle delivery tables intentionally remain separate.
Their workers and queue semantics are also independent.

## Decision

Introduce a unified read-only notification delivery observability layer.

The observability layer does not merge or replace the underlying persistence
models.

### Delivery history

Expose:

`GET /api/v1/notifications/deliveries`

The endpoint provides a workspace-scoped view across:

- backup deliveries;
- agent lifecycle deliveries.

Supported filters include:

- source;
- status;
- bounded result limit.

Results are ordered newest first.

The API normalizes both persistence models into one delivery representation.

### Delivery health

Expose:

`GET /api/v1/notifications/deliveries/health`

The health response includes aggregate counts for:

- all delivery sources;
- backup;
- agent lifecycle.

It reports:

- pending;
- sending;
- delivered;
- failed;
- canceled;
- retryable failures;
- exhausted failures;
- stale sending deliveries.

Health is degraded when any of the following are present:

- retryable delivery failures;
- exhausted delivery retries;
- stale sending claims.

Normal pending or actively sending deliveries do not independently degrade
health.

The stale sending threshold follows the existing queue claim timeout:

`300 seconds`

### Problem view

Expose:

`GET /api/v1/notifications/deliveries/problems`

This endpoint returns only deliveries requiring operational attention.

Problem classifications are:

- `retryable_failed`;
- `exhausted_failed`;
- `stale_sending`.

Successful, canceled, normally pending, and non-stale sending deliveries are
excluded.

### Authorization

All notification delivery observability endpoints require:

`workspace.read`

All results are scoped to the authenticated workspace.

### No remediation

The observability API is strictly read-only.

It does not:

- retry deliveries;
- cancel deliveries;
- modify destinations;
- modify routing;
- invoke workers;
- perform infrastructure actions;
- authorize automatic remediation.

Delivery degradation does not change `/ready` semantics.

`/ready` remains infrastructure readiness for DB and Redis.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- operators can inspect notification delivery history from one API;
- both delivery pipelines have a common operational view;
- retry exhaustion is directly visible;
- stale worker claims are observable;
- problem-focused queries avoid requiring clients to reconstruct queue
  semantics;
- no database migration is required.

### Tradeoffs

- backup and lifecycle persistence remain separate;
- aggregate observability executes queries against both delivery tables;
- health is observational and does not repair queue state;
- historical delivery volume requires bounded listing queries.

## Database

No migration is introduced.

Alembic head remains:

`0019_agent_lifecycle_deliveries`
