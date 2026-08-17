# v0.1.37-alpha

## Summary
Prevents stale runtime release versions from passing release metadata verification.

## Changes
- detects release notes newer than the configured runtime API version
- compares alpha release versions numerically rather than lexicographically
- rejects release version regressions in CI
- adds regression coverage for normal and multi-digit patch versions
- advances the runtime API version and README milestone to `0.1.37-alpha`

## Validation
- exact CI dependency baseline: 49 pins verified
- release metadata consistency verified
- full API suite: 320 passed
- pip check, compile, critical Ruff and whitespace checks passed

## Runtime / database
- runtime/API version: `0.1.37-alpha`
- package metadata remains unchanged
- no dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
- `/ready` semantics unchanged
