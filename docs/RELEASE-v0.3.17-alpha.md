# v0.3.17-alpha

## Summary

`v0.3.17-alpha` adds Manual Action Plan Control to the Web Control Center.

Operators can now create a policy-controlled infrastructure action plan directly from the Actions page using the existing backend action-plan contract.

## Web Control Center

The Actions page now supports manual creation of an action plan for the currently allowlisted capability:

- `docker.container.restart`

The UI only offers resources where:

- an active agent is visible;
- the agent advertises `docker.container.restart`;
- Docker telemetry is available;
- at least one observed Docker container is present.

Container selection is derived from the latest observed agent Docker inventory instead of free-form operator input.

The operator may provide an optional rationale up to the existing backend limit.

Creating the plan does not execute the mutation. The backend creates the plan with:

- status `pending_approval`;
- policy-derived risk level;
- policy-derived approval requirement.

Execution continues through the existing approval, task, verification and audit flow.

## Existing backend contract

The feature uses:

`POST /api/v1/action-plans`

Permission:

`action.create`

Request fields:

- `resource_id`
- `capability`
- `parameters`
- optional `rationale`

The backend allowlists `docker.container.restart`.

For Docker restart plans, the backend validates:

- the resource belongs to the active workspace;
- an active agent exists;
- the capability is allowed by policy;
- the agent advertises the capability;
- the container name matches the allowlisted format;
- the container exists in the latest observed inventory.

The backend records the existing audit action:

`action_plan.create`

## Security and policy

No direct execution path was added.

The UI does not bypass:

- workspace authorization;
- capability allowlisting;
- Policy Engine decisions;
- explicit approval;
- agent capability checks;
- backend inventory validation;
- audit logging.

The final enforcement remains server-side.

## Scope

Frontend functional changes:

- `apps/web/src/api/actions.ts`
- `apps/web/src/pages/Actions.tsx`

Release metadata changes:

- `README.md`
- `apps/api/app/version.py`
- `apps/api/pyproject.toml`
- `docs/RELEASE-v0.3.17-alpha.md`

No backend functional changes.

No database model changes.

No Alembic migration changes.

No dependency changes.

Runtime topology is unchanged.

Alembic head remains:

`0021_worker_operational_state`
