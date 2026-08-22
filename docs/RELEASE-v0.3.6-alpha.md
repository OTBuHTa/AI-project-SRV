# v0.3.6-alpha

## Summary

v0.3.6-alpha adds notification route management to the Web Control Center using the existing notification route API.

Workspace operators can create, edit, enable, disable and delete notification routing rules directly from the Notifications page.

## Route management

The Web client now integrates the existing endpoints:

- `POST /api/v1/notifications/routes`
- `PATCH /api/v1/notifications/routes/{route_id}`
- `DELETE /api/v1/notifications/routes/{route_id}`

Route listing continues to use:

- `GET /api/v1/notifications/routes`

## Supported route contract

Creation supports:

- `destination_id`
- `alert_code`
- `severity`
- `enabled`

Editing supports:

- `alert_code`
- `severity`
- `enabled`

`destination_id` is selected when a route is created and is not mutable through the existing update contract.

Empty alert code and severity values are submitted as `null`, preserving the existing wildcard routing semantics.

## Web behavior

The Notifications page now supports:

- selecting an existing notification destination when creating a route;
- creating routes with optional alert code and severity filters;
- editing alert code and severity;
- enabling and disabling routes;
- deleting routes;
- per-operation pending states;
- mutation failure feedback;
- refreshing route configuration after successful mutations.

The existing destination management introduced in v0.3.5-alpha remains unchanged.

## Authorization

Route listing uses the existing `workspace.read` permission.

Create, update and delete operations use the existing `workspace.manage` permission.

No authorization contract is changed by this release.

## Backend contracts

No backend API endpoint is added or modified.

No database model is changed.

No Alembic revision is added.

No dependency is added.

## HTTP behavior

Route deletion uses the existing `204 No Content` API response.

The shared Web `apiJson` client already accepts successful empty responses by resolving failed JSON parsing to `null`, so no shared HTTP client change is required.

## Validation

The release preserves:

- API regression coverage;
- Web lint validation;
- Web TypeScript production build;
- existing workspace isolation;
- existing RBAC contracts;
- immutable route destination behavior.

## Runtime

Docker Compose topology is unchanged.

Database head remains:

`0021_worker_operational_state`

## Release identity

- API version: `0.3.6-alpha`
- Python package version: `0.3.6a0`
