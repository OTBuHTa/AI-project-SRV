# v0.3.13-alpha

## Summary

This release adds operator-controlled backup retention cleanup to the
AI-project SRV Backup Control Center using the existing backend cleanup
contract.

The feature extends the existing frontend only, apart from release identity
metadata.

## Backup retention cleanup

The Backups page now exposes the existing retention cleanup capability:

- `POST /api/v1/backups/cleanup`;
- workspace-scoped execution;
- `workspace.manage` permission enforced by the backend;
- explicit operator confirmation before execution;
- retention values sourced from the active backup schedule;
- pending-state protection against duplicate submission;
- cleanup result reporting;
- backup data refresh after successful cleanup.

## Cleanup policy

The frontend sends the existing backend payload:

- `keep_last`;
- `max_age_days`.

When a backup schedule exists, those values are taken directly from:

- `retention_keep_last`;
- `retention_max_age_days`.

The frontend does not calculate which artifacts are eligible for deletion.
Retention selection and deletion remain backend responsibilities.

## Cleanup result

The existing API response is surfaced using:

- `deleted_files`;
- `deleted_records`.

No additional cleanup status or deletion telemetry is invented.

## Safety

Cleanup requires an explicit browser confirmation before the request is sent.

The UI does not bypass backend authorization and does not introduce direct
filesystem deletion, arbitrary path selection, force deletion, restore
deletion, or retention-policy overrides.

## Existing backup operations

Existing backup capabilities remain unchanged, including:

- manual backup execution;
- backup health;
- restore verification status;
- storage health;
- automated schedules;
- retention configuration;
- protection status;
- active and historical alerts;
- alert acknowledgement;
- backup job history.

## Backend and schema impact

- backend functional delta: none;
- Alembic delta: none;
- dependency delta: none;
- runtime topology: unchanged;
- current Alembic head remains `0021_worker_operational_state`.

## Frontend impact

Changed functional files:

- `apps/web/src/api/backups.ts`;
- `apps/web/src/pages/Backups.tsx`.

No CSS change is required.

## Validation

Release validation requires:

- exact cleanup API-client contract;
- existing backend cleanup route and schema contract;
- confirmation and schedule-derived retention UI contract;
- no backend functional delta;
- no Alembic delta;
- no dependency delta;
- Web ESLint;
- Web TypeScript/Vite production build;
- API regression suite;
- release metadata validation;
- `git diff --check`.

## Release identity

- API version: `0.3.13-alpha`
- Python package version: `0.3.13a0`
