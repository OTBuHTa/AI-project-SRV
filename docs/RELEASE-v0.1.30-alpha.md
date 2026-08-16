# v0.1.30-alpha

## Summary

v0.1.30-alpha strengthens Python dependency validation in the API
continuous-integration pipeline.

## Changes

### Dependency integrity gate

CI now runs:

`python -m pip check`

immediately after installing the API and development dependencies.

The build fails if installed packages have missing or incompatible
requirements.

### Dependency policy

No dependency versions are upgraded in this release.

Direct runtime and development dependencies continue to use bounded
version ranges in `pyproject.toml`.

Major-version upgrades such as pytest 9 or Redis client 8 remain outside
the currently declared compatibility ranges and are not introduced
implicitly.

A reproducible lock/constraints strategy is intentionally deferred to a
separate change because it affects dependency-management policy rather
than only CI validation.

## Validation

- `python -m pip check` passed with no broken requirements.
- Python compile validation passed.
- Ruff correctness gate passed.
- API test suite: 308 passed.
- One known Starlette/httpx deprecation warning remains.
- `git diff --check` passed.
- GitHub Actions dependency-integrity run passed.

## Database

No database migration is included.

Alembic head remains:

`0021_worker_operational_state`

## Readiness

`/ready` semantics are unchanged.

Readiness continues to represent PostgreSQL and Redis infrastructure
readiness only.
