# v0.3.9-alpha

## Summary

v0.3.9-alpha adds administrative agent revocation to the Web Control Center using the existing workspace-scoped agent management API.

## Agent revocation

The Web client now integrates:

- `POST /api/v1/agents/{agent_id}/revoke`

The existing backend requires:

- `agent.revoke`

The operation remains workspace-scoped.

## Response

The existing API returns:

- `agent_id`
- `revoked_at`

## Backend behavior

The existing backend revocation contract:

- marks the agent as `revoked`;
- sets `revoked_at`;
- marks the linked resource `offline`;
- invalidates any pending token rotation;
- is idempotent for an already revoked agent;
- records the operation through the existing audit path.

## Web behavior

The Agents page now provides:

- explicit revoke action per agent;
- confirmation before revocation;
- warning that credentials will be invalidated;
- warning that pending token rotation is cancelled;
- warning that the linked resource becomes offline;
- pending state while revocation is running;
- error feedback;
- successful revocation feedback;
- agent and lifecycle data refresh after success.

Actions are disabled for agents already reported as revoked.

## Rotation integration

Agent token rotation from v0.3.8-alpha remains unchanged.

If the operator revokes the same agent whose newly rotated token is still visible in ephemeral page state, that token is immediately removed from the UI.

## Secret handling

This release does not add persistent storage or logging of agent credentials.

No new use of:

- `localStorage`
- `sessionStorage`
- console logging

is introduced by the revocation implementation.

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
- `agent.revoke` authorization;
- existing agent token rotation behavior;
- ephemeral secret handling.

## Runtime

Docker Compose topology is unchanged.

Database head remains:

`0021_worker_operational_state`

## Release identity

- API version: `0.3.9-alpha`
- Python package version: `0.3.9a0`
