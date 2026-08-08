# ADR-006: Security and identity baseline

Status: Accepted

## Decision
- JWT access tokens are short-lived (15 minutes by default).
- Refresh tokens are opaque random values; only SHA-256 hashes are stored.
- Workspace membership is mandatory for workspace-scoped access.
- Roles resolve to explicit permissions rather than route-specific role checks.
- Mutating infrastructure capabilities will be evaluated by a separate policy/approval layer.
- Audit events form a hash chain (`previous_hash` -> `hash`) to make modification detectable.
- Bootstrap is intended only for the first owner and must be disabled after initialization in externally exposed environments.

## Consequences
The platform has a stable tenant-isolation and authorization boundary before agents or external users are added.
