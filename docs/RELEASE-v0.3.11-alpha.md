# v0.3.11-alpha

## Summary

v0.3.11-alpha strengthens the Audit Control Center using the existing workspace-scoped audit API.

## Existing API contract

The Web Control Center continues to use:

- `GET /api/v1/audit?limit=<n>`

The endpoint requires:

- permission `audit.read`;
- workspace scope;
- limit clamped by the backend to `1..500`;
- newest-first ordering by `created_at`.

No new audit endpoint is introduced.

## Audit Control Center

The Audit page now provides:

- loaded event count;
- distinct action count;
- distinct actor count;
- previous-hash metadata count;
- local search across the currently loaded event window;
- selectable load limits of 100, 250, or 500;
- action visibility;
- actor visibility;
- target type and target ID visibility;
- request ID visibility;
- event ID visibility;
- result visibility;
- event hash visibility;
- previous-hash visibility;
- explicit server-ordering information.

## Search and pagination

The current audit API does not provide server-side filtering.

Search in the Web Control Center is therefore local to the events already returned by the current API request.

The current audit API does not expose cursor pagination.

No pagination capability is invented by the Web client.

## Hash-chain semantics

Audit events are hashed with SHA-256 when written.

Each stored event contains:

- `hash`;
- `previous_hash`.

The current backend append implementation selects the previous `AuditLog` globally rather than filtering that lookup by workspace.

The read endpoint itself remains workspace-scoped.

Because the API does not expose server-side integrity verification, the Web Control Center presents hash-chain values only as stored metadata.

The UI does not claim that a workspace-local chain is verified, valid, complete, or broken.

## Backend contracts

No backend functional code is changed.

No audit API route is changed.

No database model is changed.

No Alembic revision is added.

No dependency is added.

The existing Web audit API client contract remains unchanged.

## Validation

The release preserves:

- API regression coverage;
- Web lint validation;
- Web TypeScript production build;
- `audit.read` permission enforcement;
- workspace-scoped audit reads;
- backend limit maximum of 500;
- newest-first audit ordering;
- existing hash and previous-hash metadata;
- no invented server filters;
- no invented pagination;
- no invented integrity-verification endpoint.

## Runtime

Docker Compose topology is unchanged.

Database head remains:

`0021_worker_operational_state`

## Release identity

- API version: `0.3.11-alpha`
- Python package version: `0.3.11a0`
