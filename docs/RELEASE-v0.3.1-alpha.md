# v0.3.1-alpha

## Summary

v0.3.1-alpha expands operational observability in the Web Control Center using existing backend contracts.

The release adds persistent backup alert history, agent lifecycle alert history and the current evaluated backup alert snapshot.

No new API endpoints, database migrations or mutation paths are introduced.

## Web Control Center

### Backup alert history

The Backups page now exposes persisted workspace backup alert events, including:

- alert code and severity;
- active or resolved state;
- message;
- first-seen and last-seen timestamps;
- resolved timestamp;
- acknowledgement timestamp and actor.

The UI uses:

- `GET /api/v1/backups/alert-events`

Access remains protected by the existing `workspace.read` permission and workspace isolation.

### Agent lifecycle alert history

The Agents page now exposes persisted lifecycle alert history, including:

- alert code and severity;
- active or resolved state;
- message;
- first-seen and last-seen timestamps;
- resolved timestamp.

The UI uses:

- `GET /api/v1/monitoring/agent-lifecycle-alert-events`

Access remains protected by the existing `agent.read` permission and workspace isolation.

### Backup alert evaluation

The Backups page now exposes the current evaluated backup alert snapshot, including:

- evaluated backup status;
- generation timestamp;
- current alert count;
- alert code, severity and message.

The UI uses:

- `GET /api/v1/backups/alerts`

Access remains protected by the existing `workspace.read` permission and workspace isolation.

## Backend contracts

This release introduces no new API endpoints.

Existing authentication, workspace isolation, RBAC, Policy Engine, approval, agent execution and audit contracts remain unchanged.

The existing backup execution mutation remains unchanged:

- `POST /api/v1/backups`

No new Web mutation is introduced by this release.

## Runtime

No database migration is added.

No dependency is added.

No Docker Compose topology change is introduced.

## Release identity

- API version: `0.3.1-alpha`
- Python package version: `0.3.1a0`
