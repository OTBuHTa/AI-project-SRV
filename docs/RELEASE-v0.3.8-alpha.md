# v0.3.8-alpha

## Summary

v0.3.8-alpha adds administrative agent token rotation to the Web Control Center using the existing agent management API.

## Agent token rotation

The Web client now integrates:

- `POST /api/v1/agents/{agent_id}/token/rotate`

The existing backend requires:

- `agent.update`

The operation remains workspace-scoped.

## Rotation response

The existing API returns:

- `agent_token`
- `agent_token_expires_at`
- `token_rotated_at`

The new token is exposed to the operator only through ephemeral React page state after a successful rotation.

## Secret handling

The Web implementation does not persist the rotated agent token to:

- `localStorage`
- `sessionStorage`

The implementation does not add token logging through console logging calls.

The token disappears when:

- the operator dismisses it;
- the page component is destroyed;
- the page is reloaded.

The backend audit contract continues to exclude the raw agent token and token hash.

## Web behavior

The Agents page now supports:

- explicit token rotation per agent;
- confirmation before rotation;
- pending state while rotating;
- error feedback;
- one-time display of the newly generated token;
- token expiry display;
- token rotation time display;
- lifecycle and agent data refresh after rotation.

Revoked agents cannot be rotated by the backend.

## Safety boundary

Agent revocation is intentionally excluded from this release.

No agent revoke client or Web action is added.

The existing two-phase self-rotation flow is unchanged.

## Backend contracts

No backend endpoint is added or modified.

No database model is changed.

No Alembic revision is added.

No dependency is added.

## Validation

The release preserves:

- API regression coverage;
- Web lint validation;
- Web TypeScript production build;
- workspace isolation;
- existing RBAC contracts;
- audit secret exclusion;
- ephemeral secret handling.

## Runtime

Docker Compose topology is unchanged.

Database head remains:

`0021_worker_operational_state`

## Release identity

- API version: `0.3.8-alpha`
- Python package version: `0.3.8a0`
