# v0.2.1-alpha

## Summary
Moves the AI-project SRV Web Control Center to a production container runtime and hardens workspace-scoped frontend/API integration and realtime authentication.

## Changes
- adds a multi-stage production Web image using Node.js build and Nginx runtime
- adds Nginx SPA fallback for protected deep links
- proxies API, health, readiness, and WebSocket traffic through the Web runtime
- exposes the production Web Control Center on port 8080
- removes the temporary Vite development runtime on port 5173
- adds workspace-aware request headers across workspace-scoped Web API clients
- fixes Resources, Agents, AI, Actions, Notifications, Backups, and Audit production requests
- preserves workspace isolation for operational API calls
- changes realtime WebSocket authentication so access tokens are no longer placed in request URLs
- authenticates realtime clients with the first WebSocket message before registering them with the workspace hub
- prevents access tokens from appearing in Nginx WebSocket request logs
- synchronizes runtime and Python package version metadata

## Validation
- full API suite: 324 passed
- Web ESLint checks passed
- Web TypeScript/Vite production build passed
- Docker API and Web images built successfully
- production Web container health check passed
- `/ready` reports database and Redis healthy
- LAN production Web smoke passed on port 8080
- workspace-scoped operational endpoints return HTTP 200
- realtime WebSocket proxy returns HTTP 101
- fresh Web/API logs contain no WebSocket token query string
- `git diff --check` passed

## Runtime / database
- runtime/API version: `0.2.1-alpha`
- Python package version: `0.2.1a0`
- production Web runtime: Nginx on container port 80, published on host port 8080
- no API dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
