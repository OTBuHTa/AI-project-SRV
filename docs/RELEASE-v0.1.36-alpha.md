# v0.1.36-alpha

## Summary
Hardens release/version consistency and prevents stale release metadata from passing CI.

## Changes
- centralizes the runtime API version in `app/version.py`
- removes duplicated runtime version literals from `app/main.py`
- adds release metadata verification for the runtime version, README current milestone and release note header
- adds 4 unit tests for release metadata verification
- adds the release metadata verifier to API CI
- refreshes the README current milestone

## Validation
- exact CI dependency baseline: 49 pins verified
- release metadata consistency verified
- full API suite: 318 passed
- pip check, compile, Ruff and whitespace checks passed

## Runtime / database
- runtime/API version: `0.1.36-alpha`
- package metadata remains unchanged
- no dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
- `/ready` semantics unchanged
