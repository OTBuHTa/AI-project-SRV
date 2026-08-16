# v0.1.32-alpha

## Summary

v0.1.32-alpha migrates the Starlette/FastAPI TestClient transport stack
from the deprecated httpx compatibility path to httpx2.

The API runtime continues to use httpx independently.

## Changes

### TestClient transport migration

The development dependency set now includes:

`httpx2>=2,<3`

The validated Python 3.12 Linux CI baseline pins:

- `httpx2==2.10.0`
- `httpcore2==2.10.0`
- `truststore==0.10.4`

The existing runtime HTTP stack remains unchanged:

- `httpx==0.28.1`
- `httpcore==1.0.9`

This separation preserves runtime HTTP behavior while allowing
Starlette TestClient to use its current supported transport stack.

### Dependency baseline

The Python 3.12 Linux CI dependency baseline now contains 49 pinned
runtime/development packages.

The existing isolated build dependency baseline remains unchanged.

## Validation

- constrained dependency installation passed locally.
- `python -m pip check` passed.
- Python compile validation passed.
- Ruff correctness gate passed.
- API test suite: 308 passed.
- no Starlette/httpx TestClient deprecation warning remains.
- `git diff --check` passed.
- GitHub Actions push CI passed on a clean Python 3.12 runner.
- GitHub Actions API test result: 308 passed with no warning.

## Runtime behavior

The runtime `httpx` dependency is intentionally retained because API
runtime services use it directly.

No application HTTP client behavior is migrated to httpx2 in this
release.

## Database

No database migration is included.

Alembic head remains:

`0021_worker_operational_state`

## Readiness

`/ready` semantics are unchanged.

Readiness continues to represent PostgreSQL and Redis infrastructure
readiness only.
