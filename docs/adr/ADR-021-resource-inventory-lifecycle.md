# ADR-021: Resource Inventory and Lifecycle Semantics

## Status

Accepted

## Context

AI-project SRV already has a canonical Resource model representing managed
infrastructure hosts.

Resources are linked to Agents, TelemetrySample records, ActionPlans,
verification logic, monitoring, and AI context.

Creating a second InfrastructureNode abstraction would duplicate host identity
and require synchronization between parallel models.

The platform also needs durable discovery of infrastructure components such as:

- CPUs;
- filesystems;
- disks;
- network interfaces;
- Docker engines;
- Docker containers;
- storage pools;
- other agent-observed components.

Inventory observations may temporarily disappear because of probe failures,
API outages, mounts, container restarts, or network interruptions.

Therefore absence from one snapshot must not immediately mean that a component
was deleted.

## Decision

### Resource remains the canonical infrastructure root

The existing `resources` table remains the canonical managed host or resource.

Inventory extends Resource rather than replacing it.

The hierarchy is:

Resource
  -> Agent
  -> ResourceInventoryItem
  -> Telemetry
  -> AI Context
  -> ActionPlan
  -> Policy Engine

### ResourceInventoryItem

A new `resource_inventory_items` table stores agent-observed infrastructure
components.

Each item includes:

- workspace identity;
- parent resource identity;
- kind;
- external identity;
- display name;
- operational status;
- JSONB attributes;
- observation timestamps;
- lifecycle state.

Inventory identity is unique by:

`resource_id + kind + external_id`

This allows idempotent snapshot reconciliation.

### Workspace isolation

Inventory reads derive workspace scope from authenticated user permission
context.

Agents cannot submit arbitrary workspace or resource identifiers.

Agent inventory ingestion derives both values from the authenticated Agent
record.

### Lifecycle states

Inventory items use three lifecycle states:

- `observed`
- `stale`
- `absent`

A newly observed item is `observed`.

The default lifecycle thresholds are:

- stale after 300 seconds without observation;
- absent after 1800 seconds without observation.

These thresholds are application policy and may become configurable later.

Items are not physically deleted when they become stale or absent.

### Snapshot reconciliation

Agent snapshots are idempotently upserted.

Observed items update:

- status;
- attributes;
- observed_at;
- last_seen_at;
- lifecycle_status.

Items not present in the current snapshot retain their previous
`last_seen_at` and are classified according to lifecycle thresholds.

Snapshot reconciliation performs one transaction commit after upsert and
classification.

### Read API

Inventory provides workspace-scoped read endpoints for:

- resource inventory items;
- kind filtering;
- lifecycle filtering;
- inventory summary;
- lifecycle summary.

Supported lifecycle filters are:

- observed;
- stale;
- absent.

## Security Properties

A user cannot select an arbitrary workspace through a query parameter.

Workspace authorization is resolved through the existing
`resource.read` permission context.

An agent token can submit inventory only for the Agent identity associated
with that token.

The API rejects an `agent_id` that does not match the authenticated Agent.

Inventory is observational state only.

It does not authorize infrastructure mutation.

The existing architectural rule remains:

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- no duplicate infrastructure-host abstraction;
- inventory integrates with existing Resource and Agent identities;
- idempotent component discovery;
- durable history of temporarily missing components;
- workspace isolation at read and ingestion boundaries;
- inventory can feed monitoring and AI context later;
- lifecycle state prevents false deletion from transient probe failures.

### Tradeoffs

- lifecycle thresholds are currently static defaults;
- absent inventory items remain stored indefinitely;
- no inventory history table exists yet;
- inventory attributes are flexible JSONB rather than strongly typed schemas;
- inventory collection capability remains agent-dependent.

## Verification

The implementation is covered by tests for:

- resource scope validation;
- idempotent inventory upsert;
- agent identity mismatch rejection;
- authenticated agent workspace/resource scoping;
- missing resource handling;
- lifecycle transitions;
- invalid lifecycle thresholds;
- workspace-scoped read behavior;
- lifecycle filter validation;
- lifecycle summary counts.

Database migrations:

- `0014_resource_inventory`
- `0015_inventory_lifecycle`

Full regression result before release finalization:

`110 passed, 1 warning`

The remaining warning is the existing Starlette TestClient/httpx deprecation
warning.
