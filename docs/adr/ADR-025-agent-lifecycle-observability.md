# ADR-025: Agent Lifecycle Observability and Failure Isolation

## Status

Accepted

## Context

AI-project SRV v0.1.19-alpha hardened the agent credential lifecycle with
two-phase rotation cleanup, administrative invalidation, recovery auditing,
and automatic removal of expired pending rotations.

The background agent lifecycle loop still had an operational weakness:
status reconciliation and token lifecycle cleanup executed in the same
database session and exception boundary.

A failure in one operation could prevent the other operation from running
during the same lifecycle iteration, and exceptions were silently discarded.

Credential lifecycle state was also primarily visible through audit events.
Administrators had no compact workspace-scoped view of current pending,
expired, incomplete, or invalid rotation state.

## Decision

v0.1.20-alpha adds explicit lifecycle failure isolation and read-only
credential lifecycle diagnostics.

### Lifecycle operation isolation

Agent status evaluation and token lifecycle cleanup now run as independent
operations.

Each operation:

- receives its own database session;
- has its own exception boundary;
- logs failures explicitly;
- does not prevent the other lifecycle operation from executing.

The lifecycle loop itself remains periodic and does not perform automatic
infrastructure remediation.

### Explicit background failure logging

Silent:

`except Exception: pass`

handling is removed from the agent lifecycle path.

Failures are logged with operation-specific messages:

- `agent status evaluation failed`
- `agent token lifecycle cleanup failed`

No credential material is included in these messages.

### Workspace-scoped token lifecycle diagnostics

A new read-only endpoint is available:

`GET /api/v1/monitoring/agent-token-lifecycle`

Access requires:

`agent.read`

The request is scoped to the workspace derived from the authenticated
permission context.

The response exposes aggregate lifecycle state including:

- total agents;
- pending rotations;
- expired pending rotations;
- incomplete pending rotations;
- revoked agents that still have pending rotation state;
- oldest pending prepare timestamp;
- prepare TTL;
- observation timestamp.

Raw tokens and token hashes are never returned.

### Pending-state invariant diagnostics

A complete pending rotation consists of:

- `pending_token_hash`
- `pending_token_expires_at`
- `token_rotation_prepared_at`

Diagnostics detect partially populated pending state as an invariant
violation.

This catches lifecycle corruption that would not be visible by checking only
for a pending token hash.

### Operational health indicator

Credential lifecycle diagnostics expose:

- `healthy`
- `degraded`

The result is `degraded` when one or more of the following conditions exists:

- expired pending rotations;
- incomplete pending rotations;
- revoked agents with pending rotation state.

A machine-readable `issues` list identifies the active conditions.

Normal in-progress pending rotation does not make the workspace degraded.

## Security Boundary

The diagnostics endpoint is read-only and workspace scoped.

It does not expose:

- raw active credentials;
- raw pending credentials;
- active token hashes;
- pending token hashes.

Lifecycle health does not grant authorization for infrastructure mutations.

Operational degradation does not trigger automatic remediation.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- lifecycle failures are no longer silently discarded;
- status evaluation and credential cleanup cannot block each other;
- administrators gain a compact view of credential lifecycle health;
- malformed pending state becomes observable;
- diagnostics remain workspace scoped and permission protected;
- no additional database migration is required.

### Tradeoffs

- lifecycle iteration opens separate database sessions for independent tasks;
- diagnostics add an aggregate database query when requested;
- lifecycle health remains observational and requires an operator or higher
  policy layer to decide what action to take.

## Verification

Verification includes:

- lifecycle failure-isolation tests;
- token cleanup regression tests;
- diagnostic aggregation tests;
- workspace-scoping tests;
- healthy and degraded status tests;
- authenticated route verification;
- full API regression;
- full Linux-agent regression;
- OpenAPI route verification;
- Python bytecode compilation;
- Alembic head verification;
- Docker Compose validation.
