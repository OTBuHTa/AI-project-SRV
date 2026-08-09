# AI-project SRV v0.1.13-alpha

## Notification Routing and Configuration

This release extends persistent backup alert delivery with workspace-scoped
notification destinations, routing rules, multi-destination delivery, and a
management API.

## Highlights

- workspace-scoped notification destinations;
- workspace-scoped notification routes;
- alert-code routing filters;
- severity routing filters;
- NULL filters as routing wildcards;
- multiple destinations per alert event;
- destination-aware delivery deduplication;
- destination-based webhook worker delivery;
- notification destination and route CRUD API;
- workspace permission enforcement;
- preservation of historical deliveries after destination deletion.

## Database

### Migration 0012

`0012_notification_routing`

Introduces:

- `notification_destinations`;
- `notification_routes`;
- nullable `destination_id` on `backup_alert_deliveries`;
- destination foreign key with `ON DELETE SET NULL`.

### Migration 0013

`0013_delivery_destination`

Changes delivery uniqueness from:

`(alert_event_id, channel)`

to:

`(alert_event_id, destination_id)`

This allows one alert event to create independent webhook deliveries to
multiple destinations.

## Routing

A route can filter on:

- alert code;
- severity.

NULL values act as wildcards.

Only enabled routes and enabled destinations participate in routing.

Routing is workspace-scoped.

## Notification API

Destinations:

- `GET /api/v1/notifications/destinations`
- `POST /api/v1/notifications/destinations`
- `PATCH /api/v1/notifications/destinations/{destination_id}`
- `DELETE /api/v1/notifications/destinations/{destination_id}`

Routes:

- `GET /api/v1/notifications/routes`
- `POST /api/v1/notifications/routes`
- `PATCH /api/v1/notifications/routes/{route_id}`
- `DELETE /api/v1/notifications/routes/{route_id}`

Permissions:

- reads require `workspace.read`;
- mutations require `workspace.manage`.

## Delivery worker

The backup alert delivery worker now resolves webhook endpoints from
`NotificationDestination`.

The global webhook URL is no longer authoritative for routed deliveries.

The worker rejects unsupported notification channels instead of attempting to
send them using webhook transport.

Missing or disabled destinations are recorded as delivery failures.

## Historical records

Deleting a notification destination does not delete historical deliveries.

The destination foreign key uses:

`ON DELETE SET NULL`

so historical delivery records remain available after configuration changes.

## Safety

Notification routing remains operational messaging only.

It does not acknowledge alerts, resolve alerts, authorize actions, or trigger
automatic remediation.

The Policy Engine remains authoritative for infrastructure mutations.

## Verification

Automated test suite:

`80 passed, 1 warning`

The warning is the existing Starlette TestClient deprecation warning and is not
specific to notification routing.

Verified against PostgreSQL:

- Alembic head `0013_delivery_destination`;
- destination and route persistence;
- alert-code and severity matching;
- mismatch rejection;
- multi-destination routing;
- per-destination delivery deduplication;
- destination-based webhook delivery;
- successful `delivered` state persistence;
- CRUD API authentication and workspace scoping;
- unknown destination rejection;
- wildcard route updates;
- historical delivery preservation with `destination_id = NULL`.

Docker Compose configuration validation:

`COMPOSE_CONFIG=PASS`

## Known limitations

- webhook is the only supported notification transport;
- webhook signing/authentication is not yet implemented;
- webhook endpoint SSRF protections are not yet implemented;
- disabled destination deliveries currently follow normal failed-delivery retry
  behavior;
- legacy nullable destination IDs remain supported for historical delivery
  compatibility.
