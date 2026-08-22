# v0.3.3-alpha

## Summary

v0.3.3-alpha adds a read-only notification delivery explorer to the Web Control Center using existing backend observability contracts.

The Notifications page can now filter delivery history and problem history while preserving cursor-based pagination for stable historical snapshots.

## Delivery explorer

The Web Control Center now supports filtering notification delivery observability by:

- source;
- delivery status;
- delivery problem;
- destination;
- channel.

The explorer uses existing read-only endpoints:

- `GET /api/v1/notifications/deliveries/page`;
- `GET /api/v1/notifications/deliveries/count`;
- `GET /api/v1/notifications/deliveries/problems/page`;
- `GET /api/v1/notifications/deliveries/problems/count`;
- `GET /api/v1/notifications/destinations`;
- `GET /api/v1/notifications/routes`.

## Pagination

Delivery and problem history use the existing cursor contracts.

The Web UI exposes Previous and Next navigation while keeping filters part of the query identity.

Automatic polling is disabled after moving away from the first cursor page so a historical snapshot is not silently replaced while the operator is paging through it.

## Counts

The explorer exposes exact filtered delivery and problem counts using the existing count endpoints.

Source-specific backup and agent lifecycle counts remain visible.

## Security and backend contracts

No backend API endpoint is added or changed.

No Web mutation is introduced.

No authentication, workspace isolation, RBAC, Policy Engine, approval, agent execution, notification delivery or audit contract is changed.

The agent task leasing endpoint is intentionally not exposed to the Web Control Center because it is authenticated as an agent and changes task execution state.

## Runtime

No Alembic revision is added.

No application dependency is added.

Docker Compose runtime topology is unchanged.

Database head remains `0021_worker_operational_state`.

## Release identity

- API version: `0.3.3-alpha`
- Python package version: `0.3.3a0`
