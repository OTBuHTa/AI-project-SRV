# v0.3.18-alpha

## Summary

`v0.3.18-alpha` adds permission-aware mutation controls to the Web Control Center.

The frontend now derives operator control availability from the active workspace role using the existing backend role-to-permission contract.

This improves UI consistency with server-side authorization while preserving the backend as the final security authority.

## Permission helper

The Web Control Center now contains a frontend permission helper matching the current backend `ROLE_PERMISSIONS` matrix.

Supported workspace roles:

- `platform_owner`
- `platform_admin`
- `organization_owner`
- `organization_admin`
- `operator`
- `analyst`
- `viewer`
- `developer`
- `billing_manager`

Wildcard access for owner roles is preserved.

Unknown or missing roles fail closed in the frontend helper.

## Permission-aware controls

### Actions

Manual action-plan creation and AI action proposals require:

`action.create`

Action-plan approval and rejection require:

`action.approve`

### Agents

Enrollment-token creation requires:

`agent.install`

Agent token rotation requires:

`agent.update`

Agent revocation requires:

`agent.revoke`

### Backups

Backup mutations require:

`workspace.manage`

This applies to the existing controls for:

- manual backup creation;
- alert acknowledgement;
- backup schedule changes;
- retention cleanup.

### Notifications

Destination and route configuration controls require:

`workspace.manage`

Read-only notification delivery observability remains available according to the existing backend read contract.

### Infrastructure

MikroTik DHCP renewal requires:

`network.execute`

Read-only RouterOS status and snapshot functionality remains separate from mutation authorization.

## Security model

Frontend permission checks are usability controls, not an authorization boundary.

The backend continues to enforce the authoritative permissions through the existing `require_permission(...)` dependencies.

No server-side permission check was removed or bypassed.

No new mutation endpoint was added.

No new executable capability was added.

## Existing backend authority

The feature aligns with the existing server-side permission contract for:

- `action.create`
- `action.approve`
- `agent.install`
- `agent.update`
- `agent.revoke`
- `workspace.manage`
- `network.execute`

The backend remains responsible for:

- authentication;
- workspace isolation;
- permission enforcement;
- policy evaluation;
- capability allowlisting;
- explicit approval where required;
- audit logging.

## Scope

Frontend functional changes:

- `apps/web/src/auth/permissions.ts`
- `apps/web/src/pages/AIAssistant.tsx`
- `apps/web/src/pages/Actions.tsx`
- `apps/web/src/pages/Agents.tsx`
- `apps/web/src/pages/Backups.tsx`
- `apps/web/src/pages/Infrastructure.tsx`
- `apps/web/src/pages/Notifications.tsx`

Release metadata changes:

- `README.md`
- `apps/api/app/version.py`
- `apps/api/pyproject.toml`
- `docs/RELEASE-v0.3.18-alpha.md`

No backend functional changes.

No database model changes.

No Alembic migration changes.

No dependency changes.

Runtime topology is unchanged.

Alembic head remains:

`0021_worker_operational_state`
