# AI-project SRV v0.1.20-alpha

## Agent Lifecycle Observability

v0.1.20-alpha improves operational visibility and resilience of the agent
lifecycle subsystem.

The release isolates lifecycle background operations, replaces silent
exception handling with explicit logging, and introduces workspace-scoped
credential lifecycle diagnostics.

## Highlights

### Failure-isolated lifecycle loop

Agent status reconciliation and token lifecycle cleanup now execute
independently.

Each operation uses:

- a separate database session;
- a separate exception boundary;
- explicit failure logging.

A failure in status evaluation no longer prevents expired token rotation
cleanup during the same lifecycle cycle.

A token lifecycle cleanup failure no longer prevents agent status evaluation.

### Background error visibility

The agent lifecycle loop no longer silently discards exceptions.

Failures are logged using operation-specific messages so runtime problems can
be diagnosed without enabling debug instrumentation.

### Agent token lifecycle diagnostics

New endpoint:

`GET /api/v1/monitoring/agent-token-lifecycle`

Required permission:

`agent.read`

Diagnostics are scoped to the authenticated workspace.

The response exposes aggregate information including:

- total agents;
- pending rotations;
- expired pending rotations;
- incomplete pending rotations;
- revoked agents with pending rotation state;
- oldest pending prepare timestamp;
- prepare TTL;
- observation timestamp.

### Pending-state invariant detection

The platform now detects partially populated pending rotation state.

A valid pending transition requires all of:

- `pending_token_hash`
- `pending_token_expires_at`
- `token_rotation_prepared_at`

Partial state is reported through:

`incomplete_pending_rotations`

### Lifecycle health state

Diagnostics expose:

`status: healthy`

or:

`status: degraded`

A degraded state is reported when diagnostics detect:

- expired pending rotations;
- incomplete pending rotation state;
- revoked agents that retain pending rotation state.

The response also includes a machine-readable `issues` list.

Normal active pending rotation inside the prepare window remains healthy.

## Database

No database migration is required.

Current Alembic head remains:

`0017_agent_token_pending`

v0.1.20-alpha reuses the token lifecycle fields introduced in earlier
releases.

## Security

The diagnostics endpoint is permission protected and workspace scoped.

It never returns raw credentials or token hashes.

Lifecycle diagnostics are observational only and do not authorize or trigger
infrastructure mutations.

**LLM advisory, Policy Engine authoritative.**

## Verification

Development verification includes:

- lifecycle loop failure-isolation tests;
- token lifecycle cleanup regression tests;
- token lifecycle diagnostic tests;
- healthy/degraded indicator tests;
- authenticated route verification;
- full API regression suite;
- full Linux-agent regression suite;
- OpenAPI route verification;
- Python bytecode compilation;
- Alembic head verification;
- Docker Compose validation and build verification.
