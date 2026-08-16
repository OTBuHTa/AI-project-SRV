# ADR-033: CI Supply-Chain Hardening

## Status

Accepted

## Context

The API CI workflow introduced in v0.1.27-alpha used GitHub Actions
major-version tags and retained checkout credentials by default.

The workflow also had no static Python correctness gate beyond bytecode
compilation and tests.

A full Ruff run against the historical codebase currently reports
significant pre-existing style and framework-specific lint debt.
Introducing all Ruff rules as a blocking gate would therefore mix
historical cleanup with CI hardening and create a large unrelated change.

## Decision

### Action runtime

Use Node.js 24-compatible GitHub Actions releases.

### Action pinning

Pin third-party workflow Actions to validated immutable commit SHAs.

This reduces exposure to unexpected action-code changes caused by
mutable version tags.

### Credential persistence

Configure checkout with:

`persist-credentials: false`

The API validation workflow performs no authenticated Git writes after
checkout.

### Lint baseline

Add the following blocking Ruff command:

`ruff check app tests --select E9,F63,F7,F82`

The initial gate is deliberately restricted to high-confidence Python
correctness failures.

Broader lint cleanup will be handled separately so historical style debt
does not become part of this CI/security change.

## Consequences

Positive:

- Node.js 20 Actions deprecation is removed.
- Action implementation revisions are deterministic.
- Git credentials are removed after checkout.
- Critical Python syntax/name errors are caught before merge.
- Existing application behavior remains unchanged.

Trade-offs:

- Pinned Actions require explicit maintenance updates.
- The critical Ruff gate does not yet represent a complete lint policy.
- Existing Ruff technical debt remains visible but non-blocking.

## Database and readiness

No database migration is required.

Alembic head remains `0021_worker_operational_state`.

The `/ready` contract is unchanged and continues to represent only
database and Redis infrastructure readiness.
