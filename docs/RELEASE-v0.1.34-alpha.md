# v0.1.34-alpha

## Summary

v0.1.34-alpha adds automated verification of the exact Python
dependency baseline used by API CI.

The CI runner now verifies that all 49 runtime/development constraint
pins are installed at exactly the expected versions.

## Changes

### Exact dependency baseline verification

Added:

`apps/api/scripts/verify_ci_constraints.py`

The verifier checks that:

- every active constraint is an exact `==` pin;
- duplicate package constraints are rejected;
- all expected 49 pins are present;
- every pinned package is installed;
- every installed version matches the pinned version.

### CI integration

GitHub Actions now runs the verifier immediately after `pip check`.

Python compile and Ruff correctness gates now also include the
`apps/api/scripts` directory.

## Validation

Local validation confirmed:

- all 49 exact pins match;
- an intentionally incorrect package version is rejected;
- an intentionally incomplete 48-pin baseline is rejected;
- `python -m pip check` passed;
- Python compile validation passed;
- Ruff correctness validation passed;
- API test suite: 308 passed;
- `git diff --check` passed.

GitHub Actions push CI also confirmed:

- exact baseline verifier passed with 49 pins;
- dependency integrity passed;
- compile validation passed;
- Ruff validation passed;
- API test suite passed with 308 tests;
- whitespace validation passed.

## Dependencies

No dependency versions are changed in this release.

The Python 3.12 Linux CI runtime/development baseline remains at
49 exact pins.

## Runtime behavior

No runtime application behavior is changed.

This release hardens CI and dependency reproducibility checks only.

## Database

No database migration is included.

Alembic head remains:

`0021_worker_operational_state`

## Readiness

`/ready` semantics are unchanged.
