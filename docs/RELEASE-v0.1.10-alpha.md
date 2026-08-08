# AI-project SRV v0.1.10-alpha

## Backup alert persistence

v0.1.10-alpha adds persistent backup alert lifecycle tracking on top of the
read-only observability introduced in v0.1.9-alpha.

Backup alerts can now be stored, resolved, re-opened, and acknowledged.

## Persistent alert events

Added persistent `backup_alert_events` with:

- workspace ID
- alert code
- severity
- message
- active state
- first seen timestamp
- last seen timestamp
- resolved timestamp
- acknowledged timestamp
- acknowledging user

Resolved alert events remain available as history.

If the same alert condition appears again after resolution, a new event is
created.

## Active alert uniqueness

Only one active alert with the same code may exist per workspace.

The database enforces this with a PostgreSQL partial unique index on:

`(workspace_id, code) WHERE active IS TRUE`

This allows multiple historical resolved events while preventing duplicate
active events.

## Alert reconciliation

Persistent alerts are synchronized by the backup scheduler worker.

The reconciliation process:

1. loads backup artifacts, jobs, and schedule state;
2. evaluates backup protection status;
3. evaluates current derived alerts;
4. creates newly observed alert events;
5. updates existing active events;
6. resolves alerts that are no longer present.

Read-only GET observability endpoints do not perform persistence writes.

## Alert acknowledgement

Added operator acknowledgement support.

Acknowledgement records:

- `acknowledged_at`
- `acknowledged_by`

Acknowledgement requires `workspace.manage`.

Acknowledgement does not resolve an alert and does not trigger remediation.

## API

Added:

- `GET /api/v1/backups/alert-events`
- `GET /api/v1/backups/alert-events/active`
- `POST /api/v1/backups/alert-events/{event_id}/acknowledge`

Read endpoints require `workspace.read`.

Alert event lookup is scoped to the current workspace.

## Database migrations

Added:

- `0009_backup_alert_events`
- `0010_backup_alert_active_unique`

`0010` replaces the initial uniqueness constraint on
`(workspace_id, code, active)` with a partial unique index covering only active
alerts.

## Validation

The persistent lifecycle was smoke-tested against PostgreSQL:

`create -> resolve -> reopen -> acknowledge`

The final database state contained:

- one resolved historical `backup_missing` event;
- one new active acknowledged `backup_missing` event.

This confirmed that resolved history is retained and the same alert code may
be safely re-opened as a new active event.

## Tests

Automated coverage includes:

- alert creation
- active alert update
- alert resolution
- acknowledgement
- missing acknowledgement target
- workspace alert reconciliation
- scheduler integration

The full API test suite passes.

## Architecture

See:

- `ADR-015 — Backup observability and alerting`
- `ADR-016 — Persistent Backup Alert Events`

Alerts remain operational state only. They do not directly authorize or
execute remediation actions.
