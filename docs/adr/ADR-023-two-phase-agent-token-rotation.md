# ADR-023: Two-Phase Agent Token Rotation

## Status

Accepted

## Context

AI-project SRV agents use expiring credentials and automated self-rotation.

The original self-rotation flow replaced the active server-side token before
the newly issued raw token was durably stored by the agent.

This created a credential-loss crash window if the process or host failed
after server commit but before local persistence.

## Decision

Agent self-rotation uses a two-phase protocol:

1. prepare;
2. durable pending credential persistence;
3. commit;
4. local promotion.

### Prepare

Endpoint:

`POST /api/v1/agents/token/rotate-self/prepare`

The agent authenticates with its current active token.

The server:

- row-locks the Agent record;
- validates active credential state;
- generates a pending token;
- stores only the pending token hash;
- records pending expiration metadata;
- records token_rotation_prepared_at;
- leaves the current token_hash unchanged;
- returns the raw pending token only once.

### Durable pending state

Before commit, the Linux agent atomically persists:

- agent_token;
- pending_agent_token;
- pending_agent_token_expires_at;
- token_rotation_prepared_at.

State persistence uses temporary-file writes, fsync, atomic replacement, and
restrictive file permissions.

### Commit

Endpoint:

`POST /api/v1/agents/token/rotate-self/commit`

The request authenticates with the pending token.

The server:

- row-locks the Agent;
- validates the pending credential;
- validates the prepare window;
- promotes pending_token_hash to token_hash;
- promotes pending expiration metadata;
- records token_rotated_at;
- clears pending rotation state.

The previous active token becomes invalid only after successful commit.

### Idempotent recovery

Commit is idempotent after successful promotion.

If the pending token was already promoted and now matches the active
token_hash, a repeated commit returns the committed token metadata.

This permits recovery after a crash between server commit and final local
state promotion.

### Local promotion

After successful server commit, the agent:

- immediately switches the in-memory active token;
- removes pending fields;
- atomically persists the promoted state.

If final persistence fails, the previously durable state still contains the
pending credential.

At startup or the next cycle, the agent detects pending_agent_token and retries
commit before heartbeat, inventory, or task polling.

### Database state

The Agent model adds:

- pending_token_hash;
- pending_token_expires_at;
- token_rotation_prepared_at.

Migration:

`0017_agent_token_pending`

Raw active and pending tokens are never stored server-side.

### Security Boundary

Credential rotation authenticates agent identity.

It does not grant arbitrary infrastructure mutation.

Mutating actions remain constrained by:

- declared capabilities;
- ActionPlan;
- Policy Engine;
- approval rules;
- verification;
- audit.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- removes the credential-loss crash window;
- preserves the active token until commit;
- supports recovery after process or host failure;
- allows idempotent commit retries;
- preserves hashed-only server-side credential storage;
- enables unattended agent token lifecycle.

### Tradeoffs

- rotation requires additional API and database state;
- the agent temporarily stores active and pending raw credentials locally;
- stale pending credentials require expiration handling;
- legacy single-phase self-rotation remains temporarily available during
  migration.

## Verification

API tests cover:

- prepare without invalidating the active token;
- pending token promotion;
- prepare expiration;
- rejection of unknown pending credentials;
- idempotent commit after promotion.

Linux-agent tests cover:

- rotation threshold detection;
- durable pending persistence;
- transport failure recovery;
- startup recovery;
- active-state preservation after prepare failure.

Database migration:

`0017_agent_token_pending`
