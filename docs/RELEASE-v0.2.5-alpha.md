# v0.2.5-alpha

## Summary

Adds controlled MikroTik network automation, strengthens Docker Compose runtime
lifecycle verification, and introduces an isolated Notion project-management
model without making Notion part of the application runtime.

## Changes

- adds a restricted RouterOS REST client for MikroTik monitoring
- exposes workspace-scoped MikroTik status and snapshot endpoints
- adds `network.read` and `network.execute` RBAC permissions
- adds WAN link, DHCP, default-route, and public-IP drift monitoring
- adds an allowlisted DHCP lease renewal recovery action
- keeps RouterOS credentials server-side
- requires HTTPS for RouterOS REST access
- keeps TLS certificate verification enabled by default
- keeps MikroTik write operations disabled by default
- prevents arbitrary RouterOS command execution
- audits successful network recovery actions
- adds MikroTik health and recovery controls to the Infrastructure UI
- adds `apps/api/scripts/mikrotik_preflight.py` for runtime validation
- adds MikroTik service tests using isolated HTTP transports
- adds Docker Compose runtime lifecycle verification
- runs lifecycle verification against a neutral environment file in CI
- documents the MikroTik automation security and activation model
- adds an isolated Notion project-management workspace model
- documents Tasks, Infrastructure, Releases, Incidents, and ADR schemas
- documents a staged future synchronization model for Notion
- keeps Notion outside the API and application runtime dependency graph

## Security

- RouterOS credentials remain server-side
- RouterOS REST access requires HTTPS
- TLS verification defaults to enabled
- network write actions default to disabled
- initial mutation scope is limited to an allowlisted DHCP renewal action
- no unrestricted RouterOS command endpoint is exposed
- network access is protected by workspace authorization and dedicated RBAC
- successful recovery actions are audited
- Notion contains no application runtime secrets or runtime dependency
- Notion availability cannot prevent AI-project-SRV from starting or serving requests

## Validation

- release metadata verification passed for `v0.2.5-alpha`
- full API test suite: 359 passed
- critical Ruff checks passed
- Python source compilation passed
- Compose build identity verification passed for all four API-based services
- Compose runtime lifecycle verification passed for seven services
- Web ESLint checks passed
- Web TypeScript/Vite production build passed
- GitHub Actions API CI passed on the integrated feature branch
- GitHub Actions Docker build identity job passed
- GitHub Actions Python 3.12 API test job passed
- git diff --check passed

## Runtime / database

- runtime/API version: `0.2.5-alpha`
- Python package version: `0.2.5a0`
- no dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
- no new runtime service topology
- Notion remains an external management layer
- MikroTik write automation remains opt-in
