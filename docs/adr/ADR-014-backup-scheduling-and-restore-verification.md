# ADR-014 — Backup scheduling and restore verification

## Decision

AI-project SRV runs scheduled backups through a dedicated scheduler service independent from the HTTP API.

Backup schedules are persisted per workspace and include:

- enabled state
- interval
- retention policy
- last run
- last successful run
- next scheduled run

The scheduler selects due rows using PostgreSQL row locking with SKIP LOCKED to reduce duplicate execution across concurrent workers.

Manual and scheduled backups share the same backup execution pipeline.

## PostgreSQL client compatibility

Backup and restore tooling must use the same PostgreSQL major version as the database server.

Current supported major version:

- PostgreSQL server: 16
- pg_dump: 16
- pg_restore: 16

The runtime rejects unsupported pg_dump major versions.

## Restore verification

A backup is marked restore_verified only after:

1. the archive is readable
2. a temporary PostgreSQL database is created
3. pg_restore completes with --exit-on-error
4. the restored Alembic revision matches the source database
5. the restored database contains the expected public schema
6. the temporary restore database is removed

Archive inspection alone is not sufficient for restore_verified status.

## Safety

- temporary restore databases use isolated generated names
- temporary databases are removed in a finally block
- production databases are never used as restore targets
- active backup jobs prevent overlapping scheduled backups for a workspace
- scheduler execution is independent from API traffic
