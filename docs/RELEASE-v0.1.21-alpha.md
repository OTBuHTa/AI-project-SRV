# AI-project SRV v0.1.21-alpha

## Agent Lifecycle Operational Alerts

v0.1.21-alpha extends agent lifecycle observability into persistent
operational alerting and notification delivery.

Credential lifecycle degradation can now be recorded as workspace-scoped
events, queried through the monitoring API, routed to notification
destinations, and delivered through the existing secured webhook transport.

No automatic infrastructure remediation is introduced.

## Highlights

### Persistent lifecycle alerts

Agent token lifecycle diagnostics now generate persistent alert events for:

- expired pending token rotations;
- incomplete pending rotation state;
- revoked agents that retain pending rotation state.

Alert codes:

- `agent_token_rotation_expired`
- `agent_token_rotation_incomplete`
- `agent_revoked_pending_rotation`

Normal in-progress rotation remains non-alerting.

### Alert history and reconciliation

Lifecycle alert events retain first-seen, last-seen, active, and resolved
state.

Only one active event per workspace and alert code is allowed.

When a condition clears, the event resolves.

If the condition later returns, a new historical event is created.

### Lifecycle reconciliation loop

Periodic lifecycle processing now independently performs:

1. agent status evaluation;
2. expired token rotation cleanup;
3. lifecycle alert reconciliation.

Each operation uses an independent database session and exception boundary.

A failure in one operation does not block the others.

### Monitoring API

New endpoints:

`GET /api/v1/monitoring/agent-lifecycle-alert-events`

`GET /api/v1/monitoring/agent-lifecycle-alert-events/active`

Required permission:

`agent.read`

Both endpoints are workspace scoped.

### Notification routing

Lifecycle alerts use the existing notification destinations and routing
rules.

Routes may select destinations by alert code and severity.

A delivery is created only when a new active lifecycle event appears.

Repeated reconciliation does not duplicate notification delivery.

A resolved and later reopened alert generates a new event and a new
notification.

### Independent lifecycle delivery queue

New table:

`agent_lifecycle_alert_deliveries`

Lifecycle delivery persistence is intentionally independent from the backup
delivery queue.

The queue supports:

- pending;
- sending;
- delivered;
- failed;
- canceled;

with bounded retries, exponential backoff, and stale sending recovery.

### Webhook worker

A dedicated Docker Compose service delivers lifecycle notifications:

`agent-lifecycle-alert-delivery`

The worker reuses the existing:

- webhook transport;
- webhook signing;
- notification endpoint validation;
- SSRF protections;
- destination enablement rules.

Unsupported channels are canceled.

Delivery failures remain operational failures and do not trigger
infrastructure actions.

## Database

Two migrations are introduced by the lifecycle alert pipeline:

`0018_agent_lifecycle_alerts`

`0019_agent_lifecycle_deliveries`

Current Alembic head:

`0019_agent_lifecycle_deliveries`

PostgreSQL verification covers:

- active-event partial uniqueness;
- lifecycle event foreign keys;
- delivery destination foreign key;
- delivery event foreign key;
- unique delivery identity;
- queue indexes;
- create, resolve, reopen, and delivery idempotency behavior.

## Security

Lifecycle notifications do not contain raw agent credentials or token hashes.

Notification endpoints remain protected by the existing endpoint policy.

Lifecycle alerts and notification delivery do not authorize infrastructure
mutation and do not implement auto-remediation.

Operational degradation does not make `/ready` fail.

**LLM advisory, Policy Engine authoritative.**

## Verification

Development verification includes:

- lifecycle evaluator tests;
- persistent lifecycle event tests;
- lifecycle monitor tests;
- lifecycle monitoring API tests;
- notification routing tests;
- delivery queue tests;
- delivery worker tests;
- webhook endpoint-policy tests;
- PostgreSQL migration and index verification;
- PostgreSQL delivery queue smoke testing;
- PostgreSQL routing/idempotency/reopen smoke testing;
- full API regression suite;
- Python bytecode compilation;
- OpenAPI route verification;
- Alembic current/head verification;
- Docker Compose validation and worker build verification.
