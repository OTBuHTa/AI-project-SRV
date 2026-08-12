# ADR-024: Agent Token Lifecycle Cleanup and Administrative Invalidation

## Status

Accepted

## Context

AI-project SRV v0.1.18-alpha introduced crash-safe two-phase agent token
rotation using prepare and commit phases.

The two-phase protocol removed the credential-loss crash window, but several
lifecycle edge cases remained:

1. the legacy single-phase self-rotation endpoint still existed;
2. an administrative token rotation could occur while a pending self-rotation
   was prepared;
3. revocation could leave pending rotation state behind;
4. expired prepare state was only cleaned when the agent attempted commit;
5. recovery and expiration paths lacked explicit audit visibility.

These conditions could leave stale or conflicting pending credential state in
the database.

## Decision

v0.1.19-alpha tightens the agent credential lifecycle around the existing
two-phase protocol.

### Remove legacy single-phase self-rotation

The endpoint:

`POST /api/v1/agents/token/rotate-self`

is removed.

Agent self-rotation now uses only:

- `POST /api/v1/agents/token/rotate-self/prepare`
- `POST /api/v1/agents/token/rotate-self/commit`

Administrative token rotation remains available through:

`POST /api/v1/agents/{agent_id}/token/rotate`

### Administrative rotation invalidates pending self-rotation

Before issuing a new administrative token, the server clears:

- `pending_token_hash`
- `pending_token_expires_at`
- `token_rotation_prepared_at`

This prevents a previously prepared pending credential from later being
committed and overriding the administrative rotation.

The administrative rotation audit record includes:

`pending_rotation_invalidated`

### Agent revocation invalidates pending self-rotation

When an agent is revoked, all pending rotation state is cleared before the
revocation is committed.

This ensures no pending credential remains valid as an unfinished lifecycle
transition after revocation.

The revocation audit record includes:

`pending_rotation_invalidated`

### Expired prepare attempts are audited

When a pending credential is presented after the prepare window has expired,
the server:

1. clears pending rotation state;
2. records an audit event;
3. rejects the commit.

Audit action:

`agent.token.rotate.prepare.expired`

Raw credentials and token hashes are not included in the audit event.

### Idempotent recovery is audited

A repeated commit using a token that has already been promoted is treated as
an idempotent recovery path.

Audit action:

`agent.token.rotate.commit.recovered`

This provides operational visibility into recovery after a lost response or
process interruption.

### Background cleanup of stale pending rotations

Expired pending rotation state is cleaned automatically by the API lifecycle
loop.

A dedicated service:

`app.services.agent_token_lifecycle.cleanup_expired_pending_rotations`

runs from the existing 30-second agent status lifecycle loop.

The cleanup selects expired pending rotations with row-level locking, clears
the pending credential state, records an audit event, and commits the cleanup.

Audit action:

`agent.token.rotate.prepare.cleanup`

Cleanup does not run in the heartbeat request path and does not require a new
database migration.

## Concurrency

Prepare, commit, administrative rotation, revocation, and lifecycle cleanup
use database row locking where credential state may be mutated.

This provides serialized transitions for a single Agent record and prevents
the background cleanup path from racing with a successful commit.

## Security Boundary

Raw agent tokens are never stored server-side.

Pending credentials remain stored only as hashes.

Audit events do not contain:

- raw active tokens;
- raw pending tokens;
- token hashes.

Credential lifecycle actions do not bypass capability, approval, policy,
verification, or audit controls for infrastructure mutations.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- removes the unsafe legacy self-rotation API;
- prevents pending credentials from overriding administrative rotation;
- prevents pending state from surviving revocation;
- removes stale pending rotation state automatically;
- improves forensic visibility of recovery and expiration events;
- requires no additional database schema changes;
- keeps cleanup outside latency-sensitive agent request paths.

### Tradeoffs

- lifecycle maintenance performs an additional database query every status
  loop interval;
- cleanup audit volume may increase when agents repeatedly prepare rotations
  but do not commit them;
- background cleanup depends on the API lifecycle loop running normally.

## Verification

Verification includes:

- API regression suite;
- Linux-agent regression suite;
- legacy route removal verification;
- administrative rotate pending invalidation tests;
- revoke pending invalidation tests;
- expired prepare audit tests;
- idempotent recovery audit tests;
- background lifecycle cleanup tests;
- Python bytecode compilation;
- Docker Compose validation;
- Alembic head verification;
- PostgreSQL token lifecycle schema verification.
