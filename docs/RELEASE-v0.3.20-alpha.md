# v0.3.20-alpha

## Summary

`v0.3.20-alpha` hardens permission-aware data access across the Web Control Center.

The release prevents frontend surfaces from issuing or presenting data that the active workspace role cannot legitimately consume, while preserving the existing backend authorization model.

Backend `require_permission(...)` enforcement remains authoritative.

## Resources

The Resources surface consumes both agent discovery and resource-backed telemetry/inventory APIs.

Its route and navigation contract now requires:

- `resource.read`
- `agent.read`

The page also applies the same checks before issuing its initial agent query.

This matches the current backend contracts:

- `GET /api/v1/agents` → `agent.read`
- `GET /api/v1/agents/{agent_id}/telemetry` → `resource.read`
- inventory APIs → `resource.read`
- resource health → `resource.read`

No backend permission semantics were changed.

## Dashboard

Dashboard remains the universal Control Center landing page.

Protected Dashboard queries continue to be permission-gated, and their associated visual surfaces are now hidden when the active role does not have access.

Protected surfaces include:

- agent state and infrastructure telemetry → `agent.read`
- action queue → `action.read`
- recent audit → `audit.read`
- backup state → `workspace.read`
- notification delivery state → `workspace.read`

This prevents intentionally disabled queries from being represented as false failures, degraded states or misleading empty data.

Public system health and readiness remain visible.

## Realtime telemetry

`useWorkspaceTelemetry` now accepts an explicit enable/disable signal.

Dashboard suppresses its workspace telemetry WebSocket when `agent.read` is absent.

The existing WebSocket authentication protocol is unchanged:

- WebSocket connects without JWT in the URL;
- authentication is sent after connection;
- invalid authentication remains rejected by the backend;
- workspace membership remains validated server-side.

The backend WebSocket contract and membership authorization are unchanged.

## AI Assistant

AI chat remains governed by `resource.read`.

Agent-backed resource context remains optional and is exposed only when `agent.read` is available.

When `agent.read` is absent:

- the agent query does not execute;
- retained agent query data is not used;
- the resource selector is disabled;
- resource context is not sent with chat requests;
- workspace AI chat remains usable without resource context.

Action proposals continue to require `action.create`.

## Security model

Frontend checks are request-suppression and UX controls only.

They do not replace backend authorization.

Existing contracts remain unchanged:

- workspace isolation;
- RBAC;
- server-side `require_permission(...)`;
- Policy Engine;
- explicit approval;
- capability allowlisting;
- action audit;
- agent authentication.

## Scope

Frontend functional changes:

- `apps/web/src/App.tsx`
- `apps/web/src/pages/AIAssistant.tsx`
- `apps/web/src/pages/Dashboard.tsx`
- `apps/web/src/pages/Resources.tsx`
- `apps/web/src/realtime/useWorkspaceTelemetry.ts`

Release metadata:

- `README.md`
- `apps/api/app/version.py`
- `apps/api/pyproject.toml`
- `docs/RELEASE-v0.3.20-alpha.md`

No backend functional changes.

No database model changes.

No Alembic migration changes.

No dependency changes.

Runtime topology is unchanged.

Alembic head remains:

`0021_worker_operational_state`
