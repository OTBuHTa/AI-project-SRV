# ADR-026: Agent Lifecycle Alert Events and Notifications

## Status

Accepted

## Context

AI-project SRV v0.1.20-alpha introduced workspace-scoped agent token
lifecycle diagnostics and explicit lifecycle failure isolation.

The diagnostics made degraded credential lifecycle state observable, but an
operator still had to poll the monitoring endpoint to discover changes.

Operational lifecycle conditions also had no persistent event history and
were not integrated with the existing notification routing system.

The existing backup notification subsystem already provides reusable
workspace-scoped destinations, alert-code and severity routing, webhook
endpoint policy, signing, retries, and delivery state.

However, backup delivery persistence is intentionally tied to
`backup_alert_events` and cannot safely represent agent lifecycle events.

## Decision

v0.1.21-alpha introduces persistent agent lifecycle alert events and an
independent lifecycle notification delivery pipeline.

### Lifecycle alert evaluation

Agent token lifecycle diagnostics are mapped to operational alerts.

The current alert codes are:

- `agent_token_rotation_expired`
- `agent_token_rotation_incomplete`
- `agent_revoked_pending_rotation`

Normal in-progress token rotation does not create an alert.

### Persistent lifecycle alert events

Lifecycle alerts are stored in:

`agent_lifecycle_alert_events`

For each workspace and alert code, at most one active event exists.

Events retain:

- workspace identity;
- alert code;
- severity;
- message;
- first-seen timestamp;
- last-seen timestamp;
- active/resolved state.

When a condition disappears, the active event is resolved.

If the same condition later returns, a new historical event is created.

### Periodic reconciliation

Lifecycle alert reconciliation runs as a separate operation in the existing
agent lifecycle loop.

Agent status evaluation, token cleanup, and lifecycle alert reconciliation
use independent database sessions and exception boundaries.

Failure in one operation does not prevent the others from executing.

Lifecycle reconciliation also includes workspaces that have an active
lifecycle alert but no remaining agents, allowing stale alerts to resolve.

### Read-only operational API

Lifecycle events are exposed through:

`GET /api/v1/monitoring/agent-lifecycle-alert-events`

and:

`GET /api/v1/monitoring/agent-lifecycle-alert-events/active`

Both endpoints require:

`agent.read`

and are scoped to the authenticated workspace.

### Notification routing

Lifecycle events reuse the existing generic notification routing rules.

Routes may match by:

- workspace;
- alert code;
- severity.

Notification destinations remain workspace scoped.

A lifecycle alert is enqueued only when a new active event is created.

Repeated reconciliation of the same active event does not create duplicate
deliveries.

A resolved condition that later reopens creates a new event and therefore a
new delivery.

### Independent delivery queue

Agent lifecycle deliveries are stored separately in:

`agent_lifecycle_alert_deliveries`

The queue intentionally does not reuse `backup_alert_deliveries`, because the
backup table has a foreign key to `backup_alert_events`.

Lifecycle delivery identity is unique by:

`(alert_event_id, destination_id)`

The queue supports:

- pending;
- sending;
- delivered;
- failed;
- canceled;

with bounded retry attempts, exponential backoff, and stale claim recovery.

### Webhook delivery

Lifecycle notification delivery reuses the existing webhook transport and
notification endpoint security policy.

The worker validates destination state and endpoint policy before delivery.

Webhook signing uses the existing notification signing configuration.

Unsupported notification channels are canceled instead of being interpreted
as executable actions.

## Security Boundary

Lifecycle alerts and notifications are operational signals only.

They do not:

- rotate credentials;
- revoke agents;
- execute infrastructure commands;
- trigger remediation;
- bypass Policy Engine authorization.

Webhook endpoints remain subject to notification endpoint validation,
including SSRF protections.

No raw token, pending token, or token hash is included in lifecycle alert
events or notification payloads.

Operational degradation never changes `/ready` semantics. Infrastructure
readiness remains based on required infrastructure dependencies.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- lifecycle degradation becomes persistent operational state;
- operators gain active and historical lifecycle event visibility;
- existing notification destinations and routing rules are reused;
- duplicate notifications are prevented for unchanged active conditions;
- reopened conditions produce distinct historical events and notifications;
- lifecycle delivery failures use bounded retry and backoff;
- backup delivery persistence remains isolated from agent lifecycle events;
- no automatic remediation is introduced.

### Tradeoffs

- lifecycle alerts require two additional persistent tables;
- notification delivery uses a separate worker and queue;
- backup and lifecycle queues currently duplicate some delivery mechanics;
- generic delivery abstraction may be considered in a future release.

## Database

v0.1.21-alpha adds:

`0018_agent_lifecycle_alerts`

and:

`0019_agent_lifecycle_deliveries`

Current Alembic head:

`0019_agent_lifecycle_deliveries`

## Verification

Verification includes:

- lifecycle alert evaluator tests;
- persistent event reconciliation tests;
- active-event uniqueness tests;
- resolve and reopen tests;
- lifecycle background failure-isolation tests;
- workspace-scoped read API tests;
- notification routing tests;
- delivery queue retry and backoff tests;
- delivery idempotency tests;
- webhook worker tests;
- endpoint security-policy tests;
- PostgreSQL migration verification;
- PostgreSQL routing and reopen smoke tests;
- full API regression;
- OpenAPI verification;
- Docker Compose validation;
- Python bytecode compilation;
- Alembic head verification.
