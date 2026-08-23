# v0.3.12-alpha — Dashboard Operations Control Center

## Summary

This release strengthens the AI-project SRV Dashboard as an operational
control-center overview using existing backend and frontend contracts only.

The release is frontend-only apart from release identity metadata.

## Dashboard

The Dashboard now exposes a compact operational summary for:

- active agents online versus enrolled active agents;
- agents currently reporting telemetry;
- pending action approvals;
- queued, executing and verifying action plans;
- notification delivery issues;
- failed and stale notification deliveries;
- failed backup jobs;
- backup storage health.

Existing detailed Dashboard panels remain available for platform readiness,
infrastructure telemetry, agents, backup protection, notification delivery,
action lifecycle and recent audit events.

## Existing data contracts

The implementation uses existing clients and backend contracts:

- agents and latest metrics;
- workspace realtime telemetry;
- backup status;
- backup health;
- backup storage health;
- backup schedule;
- notification delivery health;
- action plans;
- recent audit events;
- API health and readiness.

No new API endpoint was introduced.

## Telemetry

Existing agent telemetry remains the source for:

- CPU percentage;
- memory percentage;
- disk percentage;
- Docker inventory summary where reported.

The Dashboard does not invent latency, traffic, throughput, GPU, cost,
request-rate or SLA telemetry.

## Agent scope

`GET /api/v1/agents` returns active, non-revoked agents because the backend
filters with `Agent.revoked_at.is_(None)`.

The Dashboard therefore reports non-online active agents and does not claim
a revoked-agent count.

## Action lifecycle

Dashboard counters are derived from existing ActionPlan states, including:

- `pending_approval`;
- `queued`;
- `executing`;
- `verifying`;
- `failed`;
- `verification_failed`;
- `rejected`.

No execution, retry, rollback or cancellation capability was added.

## Backend and schema impact

- backend functional delta: none;
- API client delta: none;
- Alembic delta: none;
- dependency delta: none;
- runtime topology: unchanged;
- current Alembic head remains `0021_worker_operational_state`.

## Validation

Release validation requires:

- API test suite;
- Web ESLint;
- Web TypeScript/Vite production build;
- `git diff --check`;
- Dashboard data-contract validation;
- ActionPlan lifecycle validation;
- active-agent scope validation;
- no-invented-dashboard-capability validation.

## Release identity

- API version: `0.3.12-alpha`
- Python package version: `0.3.12a0`
