# v0.3.21-alpha

## Summary

`v0.3.21-alpha` adds server-side permission enforcement to workspace realtime telemetry.

The WebSocket endpoint now requires `resource.read` after validating the access token and workspace membership and before registering the connection with the realtime hub.

## Realtime authorization

Endpoint:

`/api/v1/monitoring/ws/{workspace_id}`

Authorization sequence:

1. accept WebSocket connection;
2. receive the post-connect authentication message;
3. validate the access token;
4. resolve the authenticated user;
5. validate membership in the requested workspace;
6. require `resource.read` for the membership role;
7. register the WebSocket with the workspace realtime hub;
8. return `auth.ok`.

JWT remains out of the WebSocket URL.

## Permission contract

Realtime `resource.telemetry` is treated as resource data and therefore follows the same read authority used by resource telemetry REST APIs:

`resource.read`

Backend `has_permission(...)` is authoritative for the WebSocket permission decision.

No role permissions were broadened or weakened.

## Close semantics

Existing close behavior is preserved:

- `4401` — invalid or malformed authentication;
- `4403` — missing workspace membership or insufficient permission.

Unauthorized connections are rejected before `hub.register(...)`.

## Regression coverage

WebSocket tests now cover:

- disconnect before authentication;
- malformed authentication;
- invalid access token;
- cross-workspace / missing membership;
- membership without `resource.read`;
- membership with `resource.read`.

The denied-role regression uses `billing_manager`.

The allowed-role regression uses `viewer`.

## Security model

Existing security contracts remain unchanged:

- workspace isolation;
- RBAC;
- server-side REST `require_permission(...)`;
- WebSocket post-connect authentication;
- Policy Engine;
- explicit approval;
- capability allowlisting;
- audit contracts;
- agent authentication.

## Scope

Functional changes:

- `apps/api/app/api/v1/monitoring.py`
- `apps/api/tests/test_monitoring_websocket_auth.py`

Release metadata:

- `README.md`
- `apps/api/app/version.py`
- `apps/api/pyproject.toml`
- `docs/RELEASE-v0.3.21-alpha.md`

No database model changes.

No Alembic migration changes.

No dependency changes.

No frontend functional changes.

Runtime topology is unchanged.

Alembic head remains:

`0021_worker_operational_state`
