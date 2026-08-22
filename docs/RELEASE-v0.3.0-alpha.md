# v0.3.0-alpha

## Summary

v0.3.0-alpha expands the Web Control Center using existing backend
contracts without adding new API endpoints, database migrations or
mutation paths.

The release adds detailed resource inventory inspection, notification
delivery problem visibility and persistent AI conversation history.

## Web Control Center

### Resource inventory detail

The Resources page now consumes the existing resource inventory item
contract and exposes:

- discovered inventory items for each resource;
- inventory kind and lifecycle filtering;
- item status and lifecycle state;
- external identifier;
- observation and last-seen timestamps;
- attribute count.

The UI uses:

- `GET /api/v1/inventory/resources/{resource_id}/items`

The existing `resource.read` permission and workspace isolation remain
unchanged.

### Notification delivery problems

The Notifications page now exposes additional delivery observability:

- total notification delivery problem count;
- backup and agent lifecycle problem counts;
- recent delivery problem records;
- destination context;
- configured route context;
- enabled destination and route state.

The UI uses:

- `GET /api/v1/notifications/deliveries/problems/page`
- `GET /api/v1/notifications/deliveries/problems/count`
- `GET /api/v1/notifications/destinations`
- `GET /api/v1/notifications/routes`

No notification management mutation is introduced by this release.

### AI conversation history

The AI Assistant now exposes persisted conversation history for the
authenticated user in the current workspace.

The UI supports:

- listing existing conversations;
- conversation title and last-updated timestamp;
- loading the selected conversation message history;
- starting a new conversation while preserving the existing chat flow.

The UI uses:

- `GET /api/v1/ai/conversations`
- `GET /api/v1/ai/conversations/{conversation_id}/messages`

Conversation access remains restricted to the authenticated user and
current workspace through the existing `resource.read` contract.

The existing `POST /api/v1/ai/chat` behavior is unchanged.

## Backend contracts

This release introduces no new API endpoints.

Existing authentication, workspace isolation, RBAC, Policy Engine,
approval, agent execution and audit contracts remain unchanged.

## Runtime

No database migration is added.

No dependency is added.

No Docker Compose topology change is introduced.

## Release identity

- API version: `0.3.0-alpha`
- Python package version: `0.3.0a0`
