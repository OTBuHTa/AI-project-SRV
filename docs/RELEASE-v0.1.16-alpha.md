# AI-project SRV v0.1.16-alpha

## Agent Security and Inventory Collection

v0.1.16-alpha hardens agent credential lifecycle and activates real inventory
collection in the Linux agent.

## Highlights

### Expiring agent tokens

Agent tokens now have a 90-day lifetime.

The server stores only token hashes and tracks:

- token_expires_at;
- token_rotated_at;
- revoked_at.

Expired agent tokens are rejected during authentication.

### Race-safe enrollment

Enrollment token consumption now uses a database row lock.

This prevents concurrent enrollment requests from successfully reusing the
same one-time credential.

### Agent token rotation

New endpoint:

`POST /api/v1/agents/{agent_id}/token/rotate`

Requires:

`agent.update`

Rotation:

- is workspace scoped;
- replaces the previous token immediately;
- creates a new 90-day expiration;
- records token_rotated_at;
- emits an audit event;
- returns the new raw token only once.

### Agent revocation

New endpoint:

`POST /api/v1/agents/{agent_id}/revoke`

Requires:

`agent.revoke`

Revocation:

- sets revoked_at;
- sets the Agent status to revoked;
- marks the linked Resource offline;
- is idempotent;
- emits an audit event.

Revoked agents can no longer authenticate for heartbeat, inventory, or task
operations.

### Linux resource inventory

The Linux agent now collects and submits persistent resource inventory.

Collected components include:

- CPU;
- memory;
- filesystems;
- network interfaces;
- Docker engine;
- Docker containers.

Snapshots are submitted through:

`POST /api/v1/agents/{agent_id}/inventory`

The server derives workspace and resource scope from the authenticated Agent.

## Database

New migration:

`0016_agent_token_security`

Current Alembic head:

`0016_agent_token_security`

## Security

Raw agent tokens are never stored server-side.

Rotation invalidates the old token immediately.

Revocation blocks future agent authentication.

Administrative operations are workspace scoped and permission protected.

Audit events do not contain raw tokens or token hashes.

**LLM advisory, Policy Engine authoritative.**

## Verification

Development verification includes:

- agent token security tests;
- enrollment security tests;
- rotation/revoke tests;
- inventory API tests;
- Linux inventory collector tests;
- full API regression suite;
- PostgreSQL schema verification;
- Alembic head verification.
