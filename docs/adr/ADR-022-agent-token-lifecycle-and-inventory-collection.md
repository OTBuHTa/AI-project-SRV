# ADR-022: Agent Token Lifecycle and Inventory Collection

## Status

Accepted

## Context

AI-project SRV agents already used:

- one-time enrollment tokens;
- hashed agent tokens;
- heartbeat authentication;
- telemetry submission;
- task polling;
- resource inventory ingestion.

The remaining gaps were:

- agent tokens had no enforced expiration;
- enrollment token consumption was not row-locked;
- administrators could not rotate agent credentials;
- administrators could not explicitly revoke agents;
- Linux agents did not submit resource inventory snapshots.

## Decision

### Agent token lifetime

New agent tokens expire after 90 days.

The Agent model stores:

- token_hash;
- token_expires_at;
- token_rotated_at;
- revoked_at.

Only token hashes are stored server-side.

Raw tokens are returned only when initially issued or rotated.

Expired tokens are rejected by agent authentication.

### Race-safe enrollment

Enrollment token lookup uses a database row lock.

This prevents concurrent requests from successfully consuming the same
one-time enrollment token.

Enrollment tokens remain bounded by:

- expiration;
- used_at state;
- workspace ownership;
- agent type.

### Token rotation

Authorized users with `agent.update` may rotate an agent token.

Rotation:

- is workspace scoped;
- rejects unknown agents with 404;
- rejects revoked agents;
- generates a new random token;
- immediately replaces the previous token hash;
- resets expiration to 90 days;
- records token_rotated_at;
- emits an audit event.

The previous raw token becomes invalid immediately.

Secrets and token hashes are not written to the audit log.

### Agent revocation

Authorized users with `agent.revoke` may revoke an agent.

Revocation:

- is workspace scoped;
- sets revoked_at;
- changes agent status to revoked;
- changes the linked Resource status to offline;
- is idempotent;
- emits an audit event.

Existing agent authentication rejects revoked agents.

This automatically blocks:

- heartbeat;
- inventory submission;
- task polling;
- task result submission.

### Linux inventory collection

The Linux agent now actively collects and submits inventory snapshots.

Inventory includes:

- CPU;
- memory;
- filesystems;
- network interfaces;
- Docker engine;
- Docker containers.

The agent derives inventory locally and submits it using its authenticated
agent identity.

The server remains authoritative for workspace and resource identity.

### Security Boundary

Agent credentials authenticate an agent identity.

They do not grant arbitrary infrastructure mutation.

Mutating actions remain constrained by:

- declared capabilities;
- ActionPlan;
- Policy Engine;
- approval rules;
- verification;
- audit.

The architectural rule remains:

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- bounded agent credential lifetime;
- race-safe one-time enrollment;
- immediate credential invalidation through rotation;
- explicit administrative revocation;
- workspace-isolated management operations;
- auditability of credential lifecycle actions;
- automatic infrastructure inventory from Linux agents.

### Tradeoffs

- agents must eventually support automated token rotation before expiration;
- rotation currently requires administrative initiation;
- agent state files still contain the raw active token locally;
- inventory collection currently runs on the heartbeat loop;
- inventory collection is Linux-agent specific.

## Verification

Security tests cover:

- token hashing;
- token expiration;
- enrollment expiration;
- enrollment reuse rejection;
- row locking;
- token rotation;
- workspace isolation;
- revoked agent rotation rejection;
- revocation;
- revocation idempotency.

Linux-agent tests cover:

- CPU inventory;
- memory inventory;
- filesystem inventory;
- network interface inventory;
- Docker engine inventory;
- Docker container inventory;
- authenticated inventory submission.

Database migration:

`0016_agent_token_security`
