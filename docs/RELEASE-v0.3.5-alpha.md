# v0.3.5-alpha

## Summary

v0.3.5-alpha adds notification destination management to the Web Control Center using the existing notification destination API.

Workspace operators can create, edit, enable, disable and delete webhook notification destinations directly from the Notifications page.

## Destination management

The Web client now integrates the existing endpoints:

- `POST /api/v1/notifications/destinations`
- `PATCH /api/v1/notifications/destinations/{destination_id}`
- `DELETE /api/v1/notifications/destinations/{destination_id}`

Destination listing continues to use:

- `GET /api/v1/notifications/destinations`

## Supported destination contract

Creation supports:

- `name`
- `channel`
- `endpoint`
- `enabled`

The current backend supports only the `webhook` notification channel.

Editing supports:

- `name`
- `endpoint`
- `enabled`

The notification channel is not mutable after creation.

## Web behavior

The Notifications page now supports:

- creating webhook destinations;
- editing destination names and endpoints;
- enabling and disabling destinations;
- deleting destinations;
- pending states for destination mutations;
- operation failure feedback;
- destination and route refresh after successful mutations;
- route-count visibility before destination deletion.

The existing backend endpoint policy continues to validate webhook endpoints.

## Delete behavior

Deleting a notification destination uses the existing database contract.

Associated notification routes are deleted through the existing `ON DELETE CASCADE` relationship.

Existing notification delivery history retains its records while its destination reference is cleared through the existing `ON DELETE SET NULL` relationship.

The Web HTTP client already tolerates successful `204 No Content` responses by resolving the parsed body as `null`; the destination delete client therefore requires no shared HTTP contract change.

## Authorization

Destination listing uses the existing `workspace.read` permission.

Create, update and delete operations use the existing `workspace.manage` permission.

No authorization contract is changed by this release.

## Backend contracts

No backend API endpoint is added or modified.

No database model is changed.

No Alembic revision is added.

No dependency is added.

Notification route CRUD is not added to the Web in this release.

## Validation

The release preserves:

- API regression coverage;
- Web lint validation;
- Web TypeScript production build;
- existing notification endpoint policy enforcement;
- existing workspace isolation and RBAC contracts.

## Runtime

Docker Compose topology is unchanged.

Database head remains:

`0021_worker_operational_state`

## Release identity

- API version: `0.3.5-alpha`
- Python package version: `0.3.5a0`
