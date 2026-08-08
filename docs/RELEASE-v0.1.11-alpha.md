# AI-project SRV v0.1.11-alpha

## Race-safe backup alert reconciliation

v0.1.11-alpha hardens persistent backup alert reconciliation against concurrent
workers.

The release removes the application-level active-alert
`SELECT -> INSERT` race and serializes the full reconciliation cycle per
workspace.

## PostgreSQL UPSERT

Persistent active alerts now use PostgreSQL:

`INSERT ... ON CONFLICT ... DO UPDATE`

The conflict target uses the existing partial unique index:

`(workspace_id, code) WHERE active IS TRUE`

If an active alert already exists, reconciliation updates its:

- severity;
- message;
- last seen timestamp.

If no active event exists, PostgreSQL creates it.

This prevents concurrent workers from producing an `IntegrityError` when both
attempt to create the same active alert.

## Workspace reconciliation lock

Backup alert reconciliation now acquires a transaction-scoped PostgreSQL
advisory lock before reading workspace backup state.

Locking uses:

`pg_advisory_xact_lock(hashtextextended(workspace_id, 0))`

The lock serializes the complete:

`snapshot -> evaluate -> persist`

cycle for a workspace.

Different workspaces can continue to reconcile concurrently.

## Lifecycle compatibility

Existing alert lifecycle semantics remain unchanged:

- create;
- update;
- resolve;
- reopen;
- acknowledge.

No database migration is required for this release.

## Validation

Automated tests cover:

- new alert UPSERT;
- existing alert UPSERT;
- multiple UPSERT operations;
- resolution;
- advisory lock invocation;
- scheduler reconciliation integration.

The complete API test suite passes with:

`58 passed`

## PostgreSQL concurrency smoke tests

### UPSERT race test

Two workers concurrently reconciled the same workspace and
`backup_missing` alert.

Result:

- `ERRORS: []`
- `ACTIVE_COUNT: 1`
- `TOTAL_EVENTS: 1`
- `RACE_TEST=PASS`

### Advisory lock test

A first transaction held the workspace advisory lock for approximately one
second.

A second transaction attempting the same lock waited approximately one second.

Result:

- no errors;
- worker wait approximately `1.0` second;
- `LOCK_TEST=PASS`

## Architecture

See:

- `ADR-016 — Persistent Backup Alert Events`
- `ADR-017 — Race-safe Backup Alert Reconciliation`

Alert reconciliation remains operational state management only and does not
trigger automatic remediation.
