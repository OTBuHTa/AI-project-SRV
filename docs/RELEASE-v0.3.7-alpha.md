# v0.3.7-alpha

## Summary

v0.3.7-alpha adds backup schedule management to the Web Control Center using the existing backup schedule API.

Workspace operators can update automated backup scheduling and retention policy directly from the Backups page.

## Backup schedule management

The Web client now integrates the existing endpoint:

- `PUT /api/v1/backups/schedule`

Schedule reading continues to use:

- `GET /api/v1/backups/schedule`

## Supported schedule contract

Updates submit the existing backend fields:

- `enabled`
- `interval_minutes`
- `retention_keep_last`
- `retention_max_age_days`

The backend remains the source of truth for validation and scheduling behavior.

When the schedule is enabled, the existing backend calculates `next_run_at`.

No scheduling semantics are implemented or duplicated in the frontend.

## Web behavior

The Backups page now supports:

- enabling or disabling the automated backup schedule;
- updating the schedule interval;
- updating retained backup count;
- updating maximum retention age;
- pending state while saving;
- failure feedback;
- success feedback;
- refreshing backup state after successful update.

The current schedule, next run and retention state remain visible in the same panel.

## Authorization

Schedule reading uses the existing `workspace.read` permission.

Schedule updates use the existing `workspace.manage` permission.

No authorization contract is changed by this release.

## Backend contracts

No backend API endpoint is added or modified.

No database model is changed.

No Alembic revision is added.

No dependency is added.

The destructive backup cleanup endpoint remains outside this release.

## Validation

The release preserves:

- API regression coverage;
- Web lint validation;
- Web TypeScript production build;
- workspace isolation;
- existing RBAC contracts;
- backend-owned schedule validation.

## Runtime

Docker Compose topology is unchanged.

Database head remains:

`0021_worker_operational_state`

## Release identity

- API version: `0.3.7-alpha`
- Python package version: `0.3.7a0`
