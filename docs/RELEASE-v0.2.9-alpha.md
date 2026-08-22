# v0.2.9-alpha

## Summary

v0.2.9-alpha expands operational visibility in the Web Control Center
using existing backend contracts.

The release adds read-only action queue visibility to the Dashboard,
backup protection and active backup alert visibility, and agent token
lifecycle diagnostics with active lifecycle alerts.

## Web Control Center

### Dashboard action queue

The Dashboard now reads the existing action-plan queue and exposes:

- action plans awaiting approval;
- queued actions;
- actions awaiting verification;
- failed execution or verification state;
- recent action plans;
- navigation to the existing Actions workflow.

The unsupported Settings placeholder was removed from the shell.

### Backup protection

The Backups page now consumes the existing read-only backup protection
contracts and exposes:

- protection status;
- restore-verification state;
- protection alerts;
- active backup alert events;
- alert severity and lifecycle timestamps.

No new backup mutation is introduced.

### Agent lifecycle diagnostics

The Agents page now consumes the existing monitoring contracts and
exposes:

- agent token lifecycle health;
- pending token rotations;
- expired token rotations;
- incomplete token rotation state;
- revoked agents retaining pending rotation state;
- active lifecycle alert events.

No status-evaluation mutation is invoked by the Web client.

## Backend contracts

This release does not introduce new API endpoints.

Existing contracts used by the new UI include:

- `GET /api/v1/action-plans`
- `GET /api/v1/backups/protection`
- `GET /api/v1/backups/alert-events/active`
- `GET /api/v1/monitoring/agent-token-lifecycle`
- `GET /api/v1/monitoring/agent-lifecycle-alert-events/active`

Authentication, workspace isolation, permission checks, Policy Engine,
approval flow and execution contracts remain unchanged.

## Runtime

No database migration is added.

No dependency is added.

No Docker Compose topology change is introduced.

## Release identity

- API version: `0.2.9-alpha`
- Python package version: `0.2.9a0`
