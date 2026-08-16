# v0.1.29-alpha

## Summary

v0.1.29-alpha removes accumulated Python correctness defects and
strengthens the CI Pyflakes correctness baseline.

## Changes

### Python correctness cleanup

Removed unused imports and unused local variables detected by Ruff.

Removed duplicate definitions of:

- `BackupCleanupRequest`
- `BackupCleanupOut`

The duplicate Pydantic schema definitions were identical, so this cleanup
does not change the API contract.

### CI correctness gate

The blocking Ruff baseline now checks:

`E9,F401,F402,F403,F404,F405,F406,F63,F7,F722,F811,F82,F821,F822,F823,F842,F901`

This adds protection against:

- unused imports
- redefinitions
- undefined names
- undefined locals
- wildcard/import consistency defects
- selected syntax and control-flow correctness errors

Broader style-oriented Ruff findings remain outside this release.

## Validation

- Python compile validation passed.
- Expanded Ruff correctness checks passed.
- API test suite: 308 passed.
- One known Starlette/httpx deprecation warning remains.
- `git diff --check` passed.
- GitHub Actions branch validation passed.

## Database

No database migration is included.

Alembic head remains:

`0021_worker_operational_state`

## Readiness

`/ready` semantics are unchanged.

Readiness continues to represent PostgreSQL and Redis infrastructure
readiness only.
