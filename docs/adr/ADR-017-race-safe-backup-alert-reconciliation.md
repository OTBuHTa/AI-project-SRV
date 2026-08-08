# ADR-017: Race-safe Backup Alert Reconciliation

## Status

Accepted

## Context

ADR-016 introduced persistent backup alert events and periodic reconciliation.

The initial implementation used a read-before-insert flow:

1. load current active alert events;
2. determine whether an event exists;
3. insert a new event when missing.

This creates a race when multiple workers reconcile the same workspace at the
same time.

Two workers may both observe that an active event does not exist and then both
attempt to insert it.

The partial unique index introduced in v0.1.10-alpha protects database
integrity, but without conflict handling one worker may receive an
`IntegrityError`.

There is also a wider reconciliation race.

Two workers may evaluate different workspace snapshots and persist them out of
order. A stale reconciliation could resolve an alert after a newer
reconciliation has already confirmed that the alert is active.

## Decision

Backup alert reconciliation uses two concurrency controls:

1. PostgreSQL UPSERT for active alert creation and refresh;
2. a transaction-scoped PostgreSQL advisory lock per workspace.

## UPSERT

Active alert persistence uses PostgreSQL:

`INSERT ... ON CONFLICT ... DO UPDATE`

The conflict target matches the existing partial unique index:

`(workspace_id, code) WHERE active IS TRUE`

When an active event already exists, reconciliation updates:

- severity;
- message;
- last seen timestamp.

When no active event exists, a new persistent event is created.

This removes the application-level `SELECT -> INSERT` race.

## Workspace advisory lock

The complete reconciliation cycle is serialized per workspace using:

`pg_advisory_xact_lock(hashtextextended(workspace_id, 0))`

The lock is acquired before loading backup artifacts, jobs, and schedule state.

This protects the complete:

`snapshot -> evaluate -> persist`

cycle from concurrent execution for the same workspace.

The advisory lock is transaction-scoped and is released automatically when the
transaction commits or rolls back.

Different workspaces use different lock keys and may still reconcile
concurrently.

## Consequences

### Positive

- concurrent alert creation does not produce duplicate active events;
- database uniqueness conflicts are handled by PostgreSQL UPSERT;
- stale reconciliation cannot overtake a newer reconciliation for the same
  workspace;
- alert lifecycle semantics from ADR-016 remain unchanged;
- no new database migration is required.

### Trade-offs

- reconciliation for the same workspace is serialized;
- a slow reconciliation delays another worker processing the same workspace;
- the implementation depends on PostgreSQL-specific UPSERT and advisory lock
  semantics.

## Verification

Unit tests cover:

- UPSERT execution for new active alerts;
- UPSERT execution for existing active alerts;
- multiple alert UPSERTs;
- alert resolution;
- workspace advisory lock invocation;
- scheduler reconciliation integration.

The full API suite passes.

Real PostgreSQL concurrency smoke tests confirmed:

### Concurrent active alert creation

Two concurrent workers reconciled the same workspace and alert code.

Result:

- zero worker errors;
- exactly one active event;
- exactly one total event;
- no `IntegrityError`.

### Workspace serialization

One transaction held the workspace advisory lock for approximately one second.

A second transaction attempting the same workspace lock waited approximately
one second before acquiring it.

This confirms that reconciliation for the same workspace is serialized.
