# v0.3.16-alpha

## Summary

`v0.3.16-alpha` adds the Platform Bootstrap Control to the Web Control Center.

The frontend now exposes the existing one-time platform bootstrap contract from the sign-in screen without adding or changing backend capabilities.

## Frontend

Updated:

- `apps/web/src/api/auth.ts`
- `apps/web/src/auth/AuthContext.ts`
- `apps/web/src/auth/AuthProvider.tsx`
- `apps/web/src/pages/Login.tsx`

The frontend now supports:

- first-time platform initialization
- initial owner email and password
- optional display name
- organization name
- organization slug
- initial workspace name
- bootstrap token session initialization
- automatic use of the single bootstrap-created workspace

The bootstrap UI is explicit and separate from normal sign-in.

## Backend contract

The release uses the existing endpoint:

`POST /api/v1/auth/bootstrap`

Response:

`201 Created`

Response model:

`TokenResponse`

Fields:

- `access_token`
- `refresh_token`
- `token_type`
- `expires_in`

Bootstrap request fields:

- `email`
- `password`
- `display_name`
- `organization_name`
- `organization_slug`
- `workspace_name`

Validation includes:

- valid email
- password length 12..128
- display name maximum 160 characters
- organization name length 2..160
- organization slug restricted by the existing lowercase alphanumeric/hyphen pattern
- workspace name length 1..160

## Bootstrap semantics

The backend remains the source of truth.

Bootstrap is available only when `bootstrap_enabled` is enabled.

If bootstrap is disabled, the endpoint returns:

`404 not_found`

If any user already exists, the endpoint returns:

`409 bootstrap_already_completed`

A successful bootstrap creates:

- one initial `User`
- one `Organization`
- one initial `Workspace`
- one `Membership`

The initial membership role is:

`ORGANIZATION_OWNER`

The organization owner is the newly created user.

The returned access token is issued with the new workspace context.

## Audit

Successful bootstrap records the existing audit action:

`platform.bootstrap`

The audit entry includes the created organization and workspace context and available request/source metadata.

## Security

The frontend does not bypass or duplicate backend bootstrap authorization or validation.

Passwords are submitted only to the existing bootstrap endpoint.

The backend validation-error handling continues to prevent password values from being echoed in validation responses.

Session tokens continue to use the existing frontend session-storage contract.

## Scope

This is a frontend functional release.

There are no functional backend API changes.

There are no database model changes.

There are no Alembic migrations.

There are no dependency changes.

There are no runtime topology changes.

Alembic head remains:

`0021_worker_operational_state`
