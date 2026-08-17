# v0.2.0-alpha

## Summary
Introduces the Web Control Center foundation for AI-project SRV, providing an authenticated workspace-scoped interface for infrastructure visibility, AI-assisted operations, controlled actions, notifications, backups, and audit history.

## Changes
- adds a React + TypeScript + Vite Web Control Center
- adds authenticated login and workspace session handling
- preserves protected deep links across login and workspace selection
- adds dashboard health and service status views
- adds resource and agent inventory with live workspace telemetry
- adds AI Assistant workflow with resource context
- adds action proposal, approval, rejection, and verification views
- adds operational notification delivery health and history
- adds backup status, storage health, schedule, and job views
- adds hash-chained audit event visibility
- adds dedicated Web CI with reproducible npm installation, lint, build, and whitespace checks
- hardens API request-validation responses against malformed Unicode input
- prevents validation errors from echoing raw request input back to clients
- adds regression coverage for malformed Unicode and sensitive validation input

## Validation
- full API suite: 324 passed
- API critical Ruff checks passed
- API dependency integrity check passed
- Web TypeScript/Vite production build passed
- Web ESLint checks passed
- release metadata consistency verified
- whitespace checks passed

## Runtime / database
- runtime/API version: `0.2.0-alpha`
- API package metadata remains unchanged
- no API dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
- existing API health/readiness semantics remain unchanged
