# ADR-016: Persistent Backup Alert Events

## Status

Accepted

## Context

ADR-015 introduced derived backup observability and alert evaluation.

Those alerts were computed from the current backup state and returned through
read-only API endpoints. They were not persisted, so the system could not
reliably answer operational questions such as:

- when an alert first appeared;
- when it was last observed;
- when it was resolved;
- whether an operator acknowledged it;
- who acknowledged it;
- whether the same alert condition later reappeared.

Persisting alert state directly from a GET endpoint would also violate normal
read-only HTTP semantics and make observability queries mutate system state.

## Decision

Introduce persistent backup alert events.

Each event records:

- workspace;
- alert code;
- severity;
- message;
- active state;
- first seen timestamp;
- last seen timestamp;
- resolved timestamp;
- acknowledgement timestamp;
- acknowledging user.

Only one active event with a given `(workspace_id, code)` may exist at a time.

This invariant is enforced by a PostgreSQL partial unique index:

```sql
CREATE UNIQUE INDEX uq_backup_alert_event_active
ON backup_alert_events (workspace_id, code)
WHERE active IS TRUE;
```

Resolved events remain in the database as history.

If the same alert code appears again after resolution, a new event is created.

## Reconciliation

Alert persistence is performed outside read-only API requests.

The backup scheduler worker invokes backup alert reconciliation for enabled
backup schedules.

For each workspace, the reconciliation flow:

1. loads current backup artifacts, jobs, and schedule state;
2. evaluates backup status;
3. evaluates derived alerts;
4. updates matching active alert events;
5. creates newly observed alert events;
6. resolves active events that are no longer present.

The existing GET observability endpoints remain read-only.

## Acknowledgement

Operators with `workspace.manage` permission may acknowledge a persistent
backup alert event.

Acknowledgement records:

- `acknowledged_at`;
- `acknowledged_by`.

Event lookup is constrained by the current workspace to prevent cross-workspace
access.

Acknowledgement does not resolve an alert and does not trigger remediation.

## API

The backup API exposes:

- `GET /api/v1/backups/alert-events`
- `GET /api/v1/backups/alert-events/active`
- `POST /api/v1/backups/alert-events/{event_id}/acknowledge`

Read operations require `workspace.read`.

Acknowledgement requires `workspace.manage`.

## Consequences

### Positive

- alert history survives process restarts;
- operators can distinguish active, resolved, and re-opened alerts;
- acknowledgement becomes auditable;
- GET observability endpoints remain side-effect free;
- database uniqueness protects against multiple active rows for the same alert
  code in a workspace.

### Trade-offs

- reconciliation adds database writes to the scheduler cycle;
- concurrent reconciliation may still require retry handling if multiple
  workers race on the same alert;
- only workspaces with enabled backup schedules are currently reconciled
  automatically;
- acknowledgement is operational metadata, not remediation.

## Verification

The implementation is verified by:

- unit tests for alert creation;
- unit tests for updating existing events;
- unit tests for resolving disappeared alerts;
- unit tests for acknowledgement;
- scheduler integration tests;
- a real PostgreSQL smoke test covering:

  `create -> resolve -> reopen -> acknowledge`

The smoke test confirmed that a resolved alert remains in history and a new
active event with the same code can be created.
