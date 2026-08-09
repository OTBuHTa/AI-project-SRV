# AI-project SRV v0.1.15-alpha

## Resource Inventory and Lifecycle

v0.1.15-alpha introduces persistent infrastructure inventory on top of the
existing Resource and Agent architecture.

## Highlights

### Persistent resource inventory

The platform can now store infrastructure components discovered by an agent.

Examples include:

- CPU;
- filesystem;
- disk;
- network interface;
- Docker engine;
- Docker container;
- storage pool.

Inventory items use the identity:

`resource_id + kind + external_id`

This makes repeated inventory snapshots idempotent.

### Agent inventory ingestion

Agents can submit inventory through:

`POST /api/v1/agents/{agent_id}/inventory`

The authenticated Agent identity determines:

- workspace_id;
- resource_id.

Agents cannot choose another workspace or managed resource.

### Workspace-scoped inventory API

Read endpoints include:

`GET /api/v1/inventory/resources/{resource_id}/items`

`GET /api/v1/inventory/resources/{resource_id}/summary`

Inventory reads use the existing `resource.read` permission boundary.

The items endpoint supports:

- kind filtering;
- lifecycle_status filtering.

### Inventory lifecycle

Inventory components now distinguish:

- observed;
- stale;
- absent.

Default thresholds:

- stale after 300 seconds;
- absent after 1800 seconds.

Missing items are not immediately deleted.

This prevents transient probe failures from being interpreted as permanent
resource removal.

### Inventory summaries

Inventory summaries expose:

- total item count;
- counts by kind;
- counts by lifecycle state.

This provides a foundation for monitoring dashboards and AI infrastructure
context.

## Database

New migrations:

- `0014_resource_inventory`
- `0015_inventory_lifecycle`

Current Alembic head:

`0015_inventory_lifecycle`

## Security

Inventory reads are workspace-scoped through permission context.

Agent ingestion is bound to the authenticated Agent identity.

Inventory remains observational state only and does not authorize remediation.

**LLM advisory, Policy Engine authoritative.**

## Verification

Validated during development:

- inventory service tests;
- agent isolation tests;
- inventory API tests;
- lifecycle transition tests;
- database migration verification;
- OpenAPI route verification.

Full regression result before release finalization:

`110 passed, 1 warning`
