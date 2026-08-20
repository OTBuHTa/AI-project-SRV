# v0.2.6-alpha

## Summary

Adds a live operations dashboard to the Web Control Center using existing
workspace-scoped telemetry and operational health APIs.

## Changes

- replaces Dashboard resource telemetry placeholders with live agent metrics
- reports online and telemetry-reporting agent counts
- shows average CPU, memory, and disk utilization for online agents
- shows observed Docker container running and total counts
- exposes workspace realtime WebSocket connection state
- exposes API build revision alongside runtime version and environment
- adds backup protection health to the Dashboard
- reports backup storage health and failed-job count
- shows backup verification and schedule state
- adds notification delivery health to the Dashboard
- reports failed, retryable, stale-sending, and issue counts
- adds the five most recent workspace audit events
- reuses existing authenticated workspace API contracts
- adds no new mutation capabilities

## Security

- workspace-scoped data continues to use existing authenticated API clients
- realtime authentication continues to send JWT credentials after WebSocket
  connection establishment rather than in the URL
- no new backend permissions are introduced
- no new write actions are introduced
- no secrets or infrastructure credentials are exposed to the browser
- existing policy, approval, audit, and workspace boundaries are unchanged

## Validation

- Web ESLint checks passed
- Web TypeScript/Vite production build passed
- GitHub Actions Web CI passed for push and pull request
- GitHub Actions Python 3.12 API tests passed for push and pull request
- GitHub Actions Docker build identity passed for push and pull request
- git diff --check passed

## Runtime / database

- runtime/API version: `0.2.6-alpha`
- Python package version: `0.2.6a0`
- no dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
- no new backend endpoint
- no new runtime service topology
- no new mutation capability
