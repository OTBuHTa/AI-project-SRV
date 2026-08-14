# AI-project SRV v0.1.22-alpha

## Notification Delivery Observability

v0.1.22-alpha adds unified operational visibility across the backup and agent
lifecycle notification delivery pipelines.

The release is observational only.

It does not introduce manual retry APIs, delivery mutation APIs, or automatic
remediation.

## Highlights

### Unified delivery history

New endpoint:

`GET /api/v1/notifications/deliveries`

Required permission:

`workspace.read`

The endpoint presents backup and agent lifecycle delivery records through one
normalized representation.

Each record includes operational information such as:

- source;
- alert event;
- channel;
- destination;
- status;
- attempt count;
- maximum attempts;
- next attempt time;
- last attempt time;
- delivered time;
- last error;
- creation and update timestamps.

Supported sources:

- `backup`
- `agent_lifecycle`

Supported statuses:

- `pending`
- `sending`
- `delivered`
- `failed`
- `canceled`

Queries may be filtered by source and status.

Result size is bounded and results are ordered newest first.

### Delivery health diagnostics

New endpoint:

`GET /api/v1/notifications/deliveries/health`

The response exposes aggregate state for:

- all notification deliveries;
- backup deliveries;
- agent lifecycle deliveries.

Metrics include:

- total;
- pending;
- sending;
- delivered;
- failed;
- canceled;
- retryable failures;
- exhausted failures;
- stale sending deliveries.

Health is reported as:

- `healthy`
- `degraded`

Machine-readable issues include:

- `notification_delivery_retryable_failure`
- `notification_delivery_retries_exhausted`
- `notification_delivery_stale_sending`

Normal queued or actively processing deliveries do not independently make
delivery health degraded.

### Problem delivery view

New endpoint:

`GET /api/v1/notifications/deliveries/problems`

The endpoint exposes only deliveries that require operational attention.

Problem classifications:

- `retryable_failed`
- `exhausted_failed`
- `stale_sending`

Normal pending, delivered, canceled, and non-stale sending records are omitted.

The view supports source filtering and bounded result limits.

### Workspace isolation

All three endpoints require:

`workspace.read`

Queries are scoped to the authenticated workspace.

Delivery data from another workspace is not included.

### Queue semantics remain authoritative

Observability follows the existing delivery queue semantics.

A failed delivery is retryable while:

`attempts < max_attempts`

It is exhausted when:

`attempts >= max_attempts`

A sending delivery becomes stale after the existing claim timeout:

`300 seconds`

No worker or queue mutation behavior is changed by this release.

## Database

No database migration is required.

Current Alembic head remains:

`0019_agent_lifecycle_deliveries`

The release reads from the existing:

- `backup_alert_deliveries`
- `agent_lifecycle_alert_deliveries`

tables.

## Security

Notification delivery observability is read-only.

The new endpoints do not:

- retry failed deliveries;
- modify delivery state;
- modify notification destinations;
- modify routing rules;
- execute infrastructure commands;
- trigger automatic remediation;
- bypass Policy Engine authorization.

Delivery degradation does not change `/ready` semantics.

**LLM advisory, Policy Engine authoritative.**

## Verification

Development verification includes:

- unified delivery history tests;
- source and status filter tests;
- workspace isolation tests;
- bounded delivery query tests;
- delivery health aggregation tests;
- retryable failure diagnostics;
- exhausted retry diagnostics;
- stale sending diagnostics;
- problem classification tests;
- notification API boundary tests;
- OpenAPI route verification;
- full API regression suite;
- Python bytecode compilation;
- Docker Compose validation;
- Alembic head verification.
