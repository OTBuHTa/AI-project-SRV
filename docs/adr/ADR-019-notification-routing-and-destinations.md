# ADR-019: Notification Routing and Destinations

## Status

Accepted

## Context

ADR-018 introduced persistent backup alert notification delivery with a single
configured webhook endpoint.

That model is sufficient for one notification target, but it does not support:

- multiple notification destinations per workspace;
- different destinations for different alert codes;
- severity-based routing;
- independent enable/disable control for destinations and routes;
- multiple webhook deliveries for the same alert event.

A workspace-scoped notification configuration layer is required without
coupling notification delivery to alert acknowledgement or infrastructure
remediation.

## Decision

Introduce workspace-scoped notification destinations and notification routes.

A notification destination defines where a notification is delivered.

A notification route defines which backup alert events are eligible for a
destination.

The initial supported transport remains:

`webhook`

## Notification destinations

Each destination records:

- ID;
- workspace ID;
- name;
- channel;
- endpoint;
- enabled state;
- creation timestamp;
- update timestamp.

Destination names are unique within a workspace.

Disabled destinations are excluded from new routing decisions.

## Notification routes

Each route records:

- ID;
- workspace ID;
- destination ID;
- optional alert code;
- optional severity;
- enabled state;
- creation timestamp;
- update timestamp.

A route matches only when:

- the route belongs to the alert workspace;
- the destination belongs to the alert workspace;
- the route is enabled;
- the destination is enabled;
- `alert_code` is NULL or equals the alert code;
- `severity` is NULL or equals the alert severity.

NULL route filters therefore act as wildcards.

Multiple matching routes for the same destination do not produce multiple
destinations.

## Delivery identity

ADR-018 defined delivery identity as:

`(alert_event_id, channel)`

This decision is superseded for routed notifications.

The new delivery identity is:

`(alert_event_id, destination_id)`

This allows one alert event to produce independent deliveries to multiple
destinations using the same channel while preventing duplicate delivery records
for the same destination.

Database uniqueness enforces this identity.

`destination_id` remains nullable for compatibility with historical delivery
records created before destination routing.

New routed deliveries always use a destination ID.

## Historical delivery preservation

Notification destinations may be deleted.

Deleting a destination:

- cascades deletion of routes referencing that destination;
- does not delete historical backup alert deliveries;
- sets `backup_alert_deliveries.destination_id` to NULL.

This preserves notification delivery history even when configuration changes.

## Worker behavior

The delivery worker resolves the destination from each queued delivery.

The worker requires:

- matching destination ID;
- matching workspace ID;
- enabled destination.

The worker sends webhook notifications to the destination endpoint rather than
to the legacy global webhook URL.

If the destination is missing or disabled, the delivery is marked failed and
follows the normal retry policy.

If the destination channel is unsupported, the delivery is marked failed
without invoking webhook transport.

The only supported transport in this release is `webhook`.

## Alert monitor integration

When reconciliation creates a new active backup alert event:

1. matching notification destinations are resolved;
2. one delivery is enqueued for each matching destination;
3. delivery uniqueness prevents duplicate queue entries.

An already-active event does not generate additional deliveries merely because
the monitor runs again.

Acknowledgement does not affect notification routing.

Notification routing does not trigger remediation.

## Management API

Workspace-scoped configuration is exposed through:

- `GET /api/v1/notifications/destinations`
- `POST /api/v1/notifications/destinations`
- `PATCH /api/v1/notifications/destinations/{destination_id}`
- `DELETE /api/v1/notifications/destinations/{destination_id}`
- `GET /api/v1/notifications/routes`
- `POST /api/v1/notifications/routes`
- `PATCH /api/v1/notifications/routes/{route_id}`
- `DELETE /api/v1/notifications/routes/{route_id}`

Read operations require:

`workspace.read`

Mutation operations require:

`workspace.manage`

All lookups are scoped to the current workspace.

A route cannot be created for a destination outside the current workspace.

## Security and safety

Notification configuration controls operational messaging only.

It does not:

- acknowledge alerts;
- resolve alerts;
- authorize infrastructure changes;
- execute actions;
- bypass the Policy Engine;
- trigger automatic remediation.

The architectural rule remains:

`LLM advisory, Policy Engine authoritative.`

Webhook endpoints are currently trusted operator configuration.

Future externally exposed destination management should add endpoint validation
and SSRF protections before arbitrary URLs are accepted from untrusted users.

## Consequences

### Positive

- one alert can notify multiple destinations;
- routing can be filtered by alert code and severity;
- destinations and routes are workspace-isolated;
- routing configuration is manageable through the API;
- delivery deduplication works independently for each destination;
- historical delivery records survive destination deletion;
- notification delivery remains independent from acknowledgement and
  remediation.

### Trade-offs

- only webhook transport is implemented;
- `destination_id` remains nullable for compatibility with historical records;
- disabled or deleted destinations cause queued deliveries to fail and retry;
- equivalent duplicate routes are possible, although routing deduplication and
  delivery uniqueness prevent duplicate deliveries;
- route workspace and destination workspace consistency is enforced by service
  and API behavior rather than a composite database foreign key;
- webhook endpoint validation and signing are not included in this release.

## Verification

Automated tests cover:

- notification route matching;
- severity mismatch;
- destination-aware delivery queue identity;
- monitor routing;
- destination-based worker delivery;
- missing or disabled destination handling;
- unsupported notification channel handling;
- notification destination and route API behavior;
- workspace isolation for destination lookup.

The full API test suite passes with:

`80 passed`

Real PostgreSQL and HTTP smoke tests confirmed:

- migration `0012_notification_routing`;
- migration `0013_delivery_destination`;
- alert code and severity routing;
- severity mismatch produces zero destinations;
- one alert routes to two destinations;
- repeated enqueue produces only one delivery per destination;
- destination-based webhook delivery reaches `delivered`;
- API authentication and `X-Workspace-ID` enforcement;
- destination create, list, patch, and delete;
- route create, list, patch, and delete;
- unknown or cross-workspace destination rejection;
- route wildcard update using NULL severity;
- deleting a destination preserves historical delivery;
- deleting a destination sets historical `destination_id` to NULL.

Alembic head:

`0013_delivery_destination`

API version:

`0.1.13-alpha`
