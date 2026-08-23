# v0.3.15-alpha

## Summary

This release adds an operator-facing agent status evaluation control to the
AI-project SRV Agents Control Center using the existing monitoring API.

The functional delta is frontend-only. The backend status evaluator,
authorization, persistence and runtime lifecycle behavior remain unchanged.

## Agent status evaluation control

The Agents page now exposes the existing endpoint:

- `POST /api/v1/monitoring/evaluate-status`;
- workspace-scoped authentication;
- backend `agent.read` authorization;
- no request payload;
- explicit operator-triggered resource status reconciliation.

The response fields are displayed directly:

- `evaluated`;
- `changed`;
- `offline_after_seconds`.

## Existing backend behavior

The existing backend status evaluator remains authoritative.

It evaluates non-revoked agents in the selected workspace and reconciles the
linked resource status using the current agent heartbeat state.

The current offline threshold is:

- `OFFLINE_AFTER_SECONDS = 90`.

Resource status is derived by the existing service as:

- `offline` when no heartbeat exists or the heartbeat is older than the
  threshold;
- `online` when the agent is currently healthy;
- `degraded` otherwise.

The backend persists changes only when at least one linked resource status
changes.

## Authorization

The existing route requires:

- `agent.read`.

The frontend does not add, bypass or reinterpret authorization rules.

The existing backend contract currently permits status reconciliation through
this permission and this release does not change that contract.

## Control Center behavior

The Agents page now provides:

- manual agent status evaluation;
- pending state while evaluation is running;
- evaluation failure feedback;
- evaluated agent count;
- changed resource count;
- backend-provided offline threshold;
- agent list refresh after successful evaluation.

No automatic frontend polling of the write endpoint is introduced.

## Existing agent controls

Existing controls remain unchanged:

- agent enrollment token creation;
- agent heartbeat telemetry;
- lifecycle diagnostics;
- lifecycle alert history;
- administrator token rotation;
- agent revocation;
- realtime workspace telemetry.

## Backend and schema impact

- backend functional delta: none;
- database schema delta: none;
- Alembic delta: none;
- dependency delta: none;
- runtime topology: unchanged;
- Alembic head remains `0021_worker_operational_state`.

## Frontend impact

Changed functional files:

- `apps/web/src/api/monitoring.ts`;
- `apps/web/src/pages/Agents.tsx`.

No CSS changes are required.

## Validation

Release validation requires:

- exact monitoring endpoint contract;
- exact `agent.read` permission contract;
- response type validation;
- status service behavior validation;
- no backend functional delta;
- no Alembic delta;
- no dependency delta;
- Web ESLint;
- Web production build;
- API regression suite;
- release metadata verification;
- `git diff --check`.

## Release identity

- API version: `0.3.15-alpha`
- Python package version: `0.3.15a0`
