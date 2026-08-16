# v0.1.33-alpha

## Summary

v0.1.33-alpha establishes a warning-free pytest baseline.

Python warnings emitted during the API test suite are now promoted to
test failures, preventing new deprecations and other warnings from
silently entering CI.

## Changes

### Warning-free pytest baseline

The pytest configuration now includes:

`filterwarnings = ["error"]`

This policy applies consistently to local pytest runs and GitHub Actions
because it is defined in `apps/api/pyproject.toml`.

### Regression verification

A controlled local probe emitted a `UserWarning` and confirmed that
pytest converted the warning into a test failure.

After removing the probe, the normal API test suite completed cleanly.

## Validation

- `python -m pip check` passed.
- Python compile validation passed.
- Ruff correctness gate passed.
- API test suite: 308 passed.
- warning gate probe failed as expected when emitting a warning.
- clean suite after the probe: 308 passed.
- `git diff --check` passed.
- GitHub Actions push CI passed on a clean Python 3.12 runner.
- GitHub Actions API test result: 308 passed.

## Dependencies

No dependency versions are changed in this release.

The Python 3.12 Linux CI baseline remains at 49 pinned
runtime/development packages.

## Runtime behavior

No runtime application behavior is changed.

The warning policy affects the test suite only.

## Database

No database migration is included.

Alembic head remains:

`0021_worker_operational_state`

## Readiness

`/ready` semantics are unchanged.

Readiness continues to represent PostgreSQL and Redis infrastructure
readiness only.
