# v0.3.19-alpha

## Summary

`v0.3.19-alpha` extends permission-aware behavior across the Web Control Center navigation, direct routes and Dashboard data loading.

The frontend now mirrors existing backend read permissions when deciding which Control Center sections are visible and reachable.

Backend permission enforcement remains authoritative.

## Permission-aware navigation

The shared Control Center navigation now hides sections when the active workspace role does not have the read permissions required by that section.

Current frontend route requirements are derived from existing backend contracts:

- Infrastructure: `agent.read` and `network.read`
- Resources: `resource.read`
- Agents: `agent.read`
- AI Assistant: `resource.read`
- Actions: `action.read`
- Notifications: `workspace.read`
- Backups: `workspace.read`
- Audit: `audit.read`

Dashboard remains available as the Control Center landing page.

Unknown or missing roles fail closed through the existing frontend permission helper.

## Direct route protection

Permission-aware navigation is not the only frontend guard.

Direct navigation to protected Control Center routes now checks the same required read permissions.

When the active workspace role does not satisfy the route contract, the frontend redirects to Dashboard instead of rendering a page that would immediately issue unauthorized API requests.

The backend remains the final authorization boundary.

## Dashboard query gating

Dashboard remains accessible across workspace roles, but protected data sources are now queried only when the active role has the corresponding backend permission.

The Dashboard applies:

- `agent.read` before loading agent state;
- `workspace.read` before loading backup state;
- `workspace.read` before loading notification delivery health;
- `action.read` before loading action plans;
- `audit.read` before loading recent audit events.

Public/system health queries remain unchanged.

This prevents avoidable permission-denied requests for roles that do not have access to individual Dashboard data sources.

## AI Assistant

The AI Assistant route now follows the backend `resource.read` contract used by:

- `POST /api/v1/ai/chat`
- `GET /api/v1/ai/conversations`
- `GET /api/v1/ai/conversations/{conversation_id}/messages`

The Assistant's agent inventory query is additionally gated by `agent.read`.

Action proposal controls continue to require `action.create`.

No new AI execution capability was added.

## Agent status evaluation

The existing Agent Status Evaluation control now checks `agent.read` before enabling the mutation.

This matches the backend contract for:

`POST /api/v1/monitoring/evaluate-status`

No backend permission was changed.

## Security and authorization

The frontend permission checks are UX and request-suppression controls.

They do not replace or bypass server-side authorization.

Existing backend `require_permission(...)` enforcement remains authoritative for every protected endpoint.

Workspace isolation, RBAC, Policy Engine behavior, action approval, capability allowlisting and audit contracts are unchanged.

## Scope

Frontend functional changes:

- `apps/web/src/App.tsx`
- `apps/web/src/pages/AIAssistant.tsx`
- `apps/web/src/pages/Agents.tsx`
- `apps/web/src/pages/Dashboard.tsx`

Release metadata changes:

- `README.md`
- `apps/api/app/version.py`
- `apps/api/pyproject.toml`
- `docs/RELEASE-v0.3.19-alpha.md`

No backend functional changes.

No database model changes.

No Alembic migration changes.

No dependency changes.

Runtime topology is unchanged.

Alembic head remains:

`0021_worker_operational_state`
