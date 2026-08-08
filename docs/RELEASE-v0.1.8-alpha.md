# AI-project SRV v0.1.8-alpha

## Backup scheduling

Added:

- persistent backup schedules
- GET /api/v1/backups/schedule
- PUT /api/v1/backups/schedule
- configurable backup interval
- persisted last run, last success and next run timestamps
- dedicated backup-scheduler service
- bounded scheduler batches
- PostgreSQL row locking with SKIP LOCKED
- active-job protection against overlapping workspace backups

## Shared execution pipeline

Manual and scheduled backups now use the same backup execution service.

Backup states use the existing lifecycle:

- running
- restore_verified
- failed

## PostgreSQL version safety

The API and scheduler now use PostgreSQL 16 client tools.

Runtime validation rejects an incompatible pg_dump major version.

## Real restore verification

restore_verified now requires an actual restore into a temporary PostgreSQL database.

Verification checks:

- archive readability
- successful pg_restore with --exit-on-error
- Alembic revision consistency
- restored public schema presence
- cleanup of temporary restore databases

## Validation

Integration smoke testing confirmed:

- due schedule detection
- scheduled backup execution
- PostgreSQL 16 dump creation
- real temporary-database restore
- restore_verified artifact state
- successful schedule last_success_at update
- next_run_at advancement
- temporary restore database cleanup
