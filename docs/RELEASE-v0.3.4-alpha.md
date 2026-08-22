# v0.3.4-alpha

## Summary

v0.3.4-alpha adds backup alert acknowledgement to the Web Control Center using the existing backup alert event API.

Operators with the existing `workspace.manage` permission can acknowledge active backup alert events directly from the Backups page.

## Backup alert acknowledgement

The Backups page now exposes an acknowledgement action for active, unacknowledged backup alert events.

The Web client uses the existing endpoint:

- `POST /api/v1/backups/alert-events/{event_id}/acknowledge`

The backend records the authenticated workspace member as `acknowledged_by` and sets the acknowledgement timestamp through the existing backup alert service.

## Web behavior

The acknowledgement control:

- is shown only for active alert events that are not already acknowledged;
- exposes a pending state for the selected alert;
- prevents duplicate interaction while that alert acknowledgement is pending;
- reports acknowledgement failures;
- reports successful acknowledgement;
- refreshes the existing Backups query after success.

The refreshed Backups state includes active alerts, alert history, protection status, health, storage, schedule and job state through the existing query contract.

## Authorization

The existing backend endpoint requires:

- authenticated workspace context;
- `workspace.manage`.

No authorization requirement is changed by this release.

## Backend contracts

No backend API endpoint is added or changed.

No database model or service contract is changed.

Existing backend tests for backup alert acknowledgement remain unchanged.

## Runtime

No Alembic revision is added.

No dependency is added.

Docker Compose runtime topology is unchanged.

Database head remains `0021_worker_operational_state`.

## Release identity

- API version: `0.3.4-alpha`
- Python package version: `0.3.4a0`
