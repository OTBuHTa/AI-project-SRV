# v0.1.28-alpha

## Summary

v0.1.28-alpha hardens the API continuous-integration pipeline and
establishes a safer baseline for future validation.

## Changes

### GitHub Actions runtime

- Upgraded `actions/checkout` from v4 to v6.
- Upgraded `actions/setup-python` from v5 to v6.
- Removes the previous Node.js 20 deprecation warning from GitHub-hosted
  Actions runs.

### Supply-chain hardening

GitHub Actions are pinned to validated commit SHAs instead of mutable
major-version references:

- `actions/checkout`
  `d23441a48e516b6c34aea4fa41551a30e30af803`
- `actions/setup-python`
  `ece7cb06caefa5fff74198d8649806c4678c61a1`

### Checkout credential minimization

The checkout step now uses:

`persist-credentials: false`

The workflow requires repository contents only for validation and does
not need Git credentials after checkout.

### Critical Python lint baseline

CI now runs:

`ruff check app tests --select E9,F63,F7,F82`

This intentionally enforces only high-confidence Python correctness
checks. Existing broader Ruff findings remain technical debt and are not
silently converted into release blockers.

## Validation

Local validation before release preparation:

- Python compile validation passed.
- Critical Ruff baseline passed.
- API test suite: 308 passed.
- One known Starlette/httpx deprecation warning remains.
- `git diff --check` passed.

GitHub Actions validation completed successfully for every incremental
CI change.

## Database

No database migration is included in this release.

Alembic head remains:

`0021_worker_operational_state`

## Readiness semantics

`/ready` semantics are unchanged.

Readiness remains limited to infrastructure dependencies:

- PostgreSQL
- Redis

Operational or business subsystem degradation does not make `/ready`
fail.
