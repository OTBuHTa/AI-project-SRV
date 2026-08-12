# AI-project SRV v0.1.18-alpha

## Crash-Safe Automatic Agent Credential Rotation

v0.1.18-alpha adds automatic Linux-agent token rotation using a two-phase
prepare/commit protocol with crash recovery.

## Highlights

### Automatic rotation

The Linux agent evaluates token expiration before each operational cycle.

Credentials entering the seven-day rotation window are automatically rotated.

### Two-phase self-rotation

New endpoints:

`POST /api/v1/agents/token/rotate-self/prepare`

`POST /api/v1/agents/token/rotate-self/commit`

Prepare:

- authenticates using the active agent token;
- creates a pending credential;
- stores only its hash server-side;
- leaves the active token valid;
- returns the raw pending token once.

Commit:

- authenticates using the pending token;
- promotes it to the active credential;
- updates expiration metadata;
- records token_rotated_at;
- clears pending server-side state.

### Crash-safe local persistence

Before commit, the agent atomically persists the pending credential.

The state file temporarily contains both the active and pending credentials.

Only after successful server commit does the agent promote the pending token
to the local active token.

### Restart recovery

If pending_agent_token exists during startup or a later cycle, the agent
attempts recovery before heartbeat, inventory, or task polling.

Commit is idempotent after promotion, allowing safe recovery after a crash
between server commit and final local persistence.

### Secure local state

Agent state uses:

- temporary-file writes;
- fsync;
- atomic replacement;
- restrictive file permissions.

Raw credentials are never stored server-side.

### ORM alignment

token_expires_at and token_rotated_at are correctly mapped to the Agent ORM
model.

## Database

New migration:

`0017_agent_token_pending`

New Agent fields:

- pending_token_hash;
- pending_token_expires_at;
- token_rotation_prepared_at.

Current Alembic head:

`0017_agent_token_pending`

## Security

The active credential remains valid until a pending credential has been
durably stored and explicitly committed.

Audit events do not contain raw credentials or token hashes.

Expired and revoked credentials remain rejected.

Administrative rotation and revocation remain permission protected and
workspace scoped.

**LLM advisory, Policy Engine authoritative.**

## Verification

Development verification includes:

- two-phase API rotation tests;
- idempotent commit recovery tests;
- pending rotation expiration tests;
- Linux-agent credential recovery tests;
- atomic state persistence tests;
- full Linux-agent regression suite;
- full API regression suite;
- PostgreSQL schema verification;
- Alembic head verification;
- Python bytecode compilation;
- Docker Compose configuration and image build verification.
