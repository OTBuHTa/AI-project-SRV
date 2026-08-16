# v0.1.31-alpha

## Summary

v0.1.31-alpha adds a reproducible Python dependency baseline for API CI.

## Changes

### Runtime and development dependency constraints

CI now installs the API using:

`constraints/ci-py312-linux.txt`

The baseline pins the complete validated runtime and development
dependency graph used by the Python 3.12 Linux CI environment.

The file currently contains 46 pinned packages.

The declared compatibility ranges in `pyproject.toml` remain unchanged.
The constraints file controls CI resolution without changing the API's
published dependency metadata.

### Isolated build constraints

PEP 517 isolated build dependencies are constrained separately through:

`constraints/build-ci-py312-linux.txt`

CI passes this file through pip's `--build-constraint` option.

The current isolated build baseline pins:

`setuptools==83.0.0`

### Cache reproducibility

The pip cache key now depends on:

- `apps/api/pyproject.toml`
- `apps/api/constraints/ci-py312-linux.txt`
- `apps/api/constraints/build-ci-py312-linux.txt`

Changing either dependency baseline therefore invalidates the relevant
CI dependency cache.

## Validation

- constrained API installation passed locally.
- all 46 runtime/development constraints matched installed versions.
- isolated build installation passed with the build constraint enabled.
- `python -m pip check` passed.
- Python compile validation passed.
- Ruff correctness gate passed.
- API test suite: 308 passed.
- One known Starlette/httpx deprecation warning remains.
- `git diff --check` passed.
- GitHub Actions runtime/development constraints run passed.
- GitHub Actions isolated build constraints run passed.

## Dependency policy

No dependency compatibility ranges in `pyproject.toml` are changed by
this release.

The package metadata version remains independent from the API runtime
release version.

The CI constraints are currently scoped to the Python 3.12 Linux CI
environment and should be deliberately regenerated when dependency
updates are accepted.

## Database

No database migration is included.

Alembic head remains:

`0021_worker_operational_state`

## Readiness

`/ready` semantics are unchanged.

Readiness continues to represent PostgreSQL and Redis infrastructure
readiness only.
