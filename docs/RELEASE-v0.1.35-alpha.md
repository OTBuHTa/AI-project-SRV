# v0.1.35-alpha

## Summary
Adds permanent unit coverage for the CI dependency baseline verifier.

## Changes
- adds 6 verifier unit tests
- covers exact pins and canonical package names
- rejects version mismatches and missing packages
- rejects non-exact and duplicate constraints
- rejects incomplete pin baselines

## Validation
- exact CI baseline: 49 pins verified
- targeted verifier tests: 6 passed
- full API suite: 314 passed
- pip check, compile, Ruff and whitespace checks passed

## Runtime / database
- no dependency changes
- no database migration
- Alembic head remains 0021_worker_operational_state
- /ready semantics unchanged
