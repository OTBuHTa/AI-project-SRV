# v0.3.10-alpha

## Summary

v0.3.10-alpha strengthens the Infrastructure Actions Control Center using only the existing policy-controlled ActionPlan API.

## Existing API contracts

The Web Control Center continues to use:

- `GET /api/v1/action-plans`
- `POST /api/v1/action-plans/{plan_id}/approve`
- `POST /api/v1/action-plans/{plan_id}/reject`

No new execution, retry, rollback, cancellation, or other mutation endpoint is introduced.

## Actions Control Center

The Actions page now provides:

- pending approval count;
- active action count;
- successful action count;
- failed/rejected action count;
- operator approval warning;
- action plan ID;
- resource ID;
- capability;
- risk level;
- approval requirement;
- source;
- lifecycle status;
- creation timestamp;
- approval timestamp;
- completion timestamp;
- verification start timestamp;
- verification completion timestamp;
- action parameters;
- rationale;
- execution result;
- verification result.

## Approval safety

Approve and reject controls remain available only while an ActionPlan is in `pending_approval`.

Approval now requires explicit operator confirmation before the existing approval mutation is submitted.

The confirmation identifies that approval authorizes the infrastructure mutation represented by the plan.

Rejection also requires explicit confirmation.

Mutations are disabled while an approval or rejection request is pending.

## Execution model

The Web Control Center does not directly execute infrastructure mutations.

Approval continues through the existing backend execution pipeline:

ActionPlan → policy/approval → queued agent task → execution → verification.

The page exposes existing backend state rather than creating unsupported capabilities.

## Backend contracts

No backend endpoint is added or modified.

No database model is changed.

No Alembic revision is added.

No dependency is added.

The existing Web API client contract remains unchanged.

## Validation

The release preserves:

- API regression coverage;
- Web lint validation;
- Web TypeScript production build;
- workspace-scoped ActionPlan access;
- existing approve/reject API contracts;
- pending-only approval controls;
- policy-controlled execution;
- existing agent task execution and verification pipeline.

## Runtime

Docker Compose topology is unchanged.

Database head remains:

`0021_worker_operational_state`

## Release identity

- API version: `0.3.10-alpha`
- Python package version: `0.3.10a0`
