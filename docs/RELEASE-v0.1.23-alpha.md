# AI-project SRV v0.1.23-alpha

## Notification Delivery Query Scalability

v0.1.23-alpha extends the notification delivery observability introduced in
v0.1.22-alpha.

The release adds scalable pagination, richer filters, and count endpoints for
operator and UI consumption.

The release remains read-only.

## Delivery history

Endpoint:

`GET /api/v1/notifications/deliveries`

Supported query capabilities now include:

- `source`;
- `status`;
- `destination_id`;
- `channel`;
- `created_from`;
- `created_to`;
- `created_from` and `created_to` must be timezone-aware ISO datetimes;
- `offset`;
- `limit`.

Results remain globally ordered newest first across backup and agent lifecycle
delivery sources.

Offset pagination is applied after the two source result sets are merged.

## Problem deliveries

Endpoint:

`GET /api/v1/notifications/deliveries/problems`

Supported query capabilities include:

- `source`;
- `problem`;
- `destination_id`;
- `channel`;
- `created_from`;
- `created_to`;
- `created_from` and `created_to` must be timezone-aware ISO datetimes;
- `offset`;
- `limit`.

Supported problem classifications:

- `retryable_failed`;
- `exhausted_failed`;
- `stale_sending`.

Only deliveries requiring operational attention are included.

## Count endpoints

New endpoints:

`GET /api/v1/notifications/deliveries/count`

`GET /api/v1/notifications/deliveries/problems/count`

Responses expose:

- `total`;
- `backup`;
- `agent_lifecycle`.

Count filters match the corresponding list views.

Problem counts use the existing queue problem semantics and do not count
healthy, delivered, canceled, normal pending, or non-stale sending records.

## Existing delivery health

The existing endpoint remains available:

`GET /api/v1/notifications/deliveries/health`

Its degradation semantics are unchanged.

## Authorization and isolation

All notification delivery query endpoints require:

`workspace.read`

All delivery and count queries are scoped to the authenticated workspace.

Backup and agent lifecycle queries remain SQL-isolated from one another.

## Safety and operational boundaries

v0.1.23-alpha introduces no delivery mutation API.

It does not:

- retry failed deliveries;
- cancel deliveries;
- modify queue state;
- modify notification destinations;
- modify routing rules;
- execute infrastructure actions;
- trigger automatic remediation.

`/ready` semantics are unchanged.

**LLM advisory, Policy Engine authoritative.**

## Database

No database migration is required.

Alembic head remains:

`0019_agent_lifecycle_deliveries`

## Verification

Release verification includes:

- delivery history pagination tests;
- global merge ordering tests;
- history filter tests;
- problem pagination tests;
- problem classification filter tests;
- count aggregation tests;
- source isolation tests;
- workspace isolation tests;
- time range validation;
- OpenAPI route and parameter validation;
- Python bytecode compilation;
- full API regression;
- Docker Compose validation;
- Alembic current/head verification.
