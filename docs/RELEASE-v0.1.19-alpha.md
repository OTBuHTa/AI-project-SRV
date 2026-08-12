# AI-project SRV v0.1.19-alpha

## Agent Credential Lifecycle Hardening

v0.1.19-alpha hardens the agent credential lifecycle introduced in
v0.1.18-alpha.

The release removes the remaining legacy self-rotation path, prevents pending
credentials from conflicting with administrative actions, adds recovery and
expiration audit visibility, and automatically removes stale pending rotation
state.

## Highlights

### Legacy self-rotation removed

Removed:

`POST /api/v1/agents/token/rotate-self`

Agent self-rotation now exclusively uses the two-phase protocol:

- `POST /api/v1/agents/token/rotate-self/prepare`
- `POST /api/v1/agents/token/rotate-self/commit`

Administrative rotation remains available separately.

### Administrative rotation safety

Administrative token rotation now invalidates any unfinished pending
self-rotation before issuing a replacement active credential.

This prevents a previously prepared token from later overriding the
administrator-issued credential.

Audit metadata records whether pending rotation state was invalidated.

### Revocation safety

Agent revocation now clears all pending token rotation state.

A revoked agent cannot retain an unfinished pending credential transition.

### Expired prepare observability

Expired prepare attempts are now explicitly audited.

Audit action:

`agent.token.rotate.prepare.expired`

The server clears expired pending state before rejecting the commit.

### Recovery observability

Idempotent commit recovery is explicitly audited.

Audit action:

`agent.token.rotate.commit.recovered`

This makes crash/lost-response recovery visible in operational audit history.

### Automatic stale pending cleanup

The API now automatically removes expired pending credential rotations.

A dedicated lifecycle service runs from the existing 30-second status loop and:

- selects expired pending rotations;
- obtains row-level locks;
- clears pending credential state;
- writes an audit record;
- commits the cleanup.

Audit action:

`agent.token.rotate.prepare.cleanup`

Cleanup does not run in heartbeat or task polling request paths.

## Database

No new migration is required.

Current Alembic head remains:

`0017_agent_token_pending`

Existing Agent lifecycle fields are used:

- `token_hash`
- `token_expires_at`
- `token_rotated_at`
- `pending_token_hash`
- `pending_token_expires_at`
- `token_rotation_prepared_at`

## Security

Raw credentials are not persisted server-side.

Administrative rotation and revocation invalidate unfinished pending
credential state.

Audit records do not contain raw credentials or token hashes.

Credential rotation remains independent from infrastructure mutation
authorization.

**LLM advisory, Policy Engine authoritative.**

## Verification

Development verification includes:

- legacy self-rotation route removal;
- two-phase rotation regression tests;
- administrative rotation invalidation tests;
- revocation invalidation tests;
- expired prepare audit tests;
- recovery audit tests;
- lifecycle cleanup tests;
- full API regression suite;
- full Linux-agent regression suite;
- PostgreSQL schema verification;
- Alembic head verification;
- Python bytecode compilation;
- Docker Compose configuration and API image build verification.
