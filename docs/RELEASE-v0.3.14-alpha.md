# v0.3.14-alpha

## Summary

This release adds operator-controlled agent enrollment token creation to the
AI-project SRV Agents Control Center using the existing backend enrollment
contract.

The functional change is frontend-only. Backend authorization, token
generation, hashing, expiration and audit behavior remain unchanged.

## Agent enrollment token control

The Agents page now exposes the existing endpoint:

- `POST /api/v1/agents/enrollment-token`;
- workspace-scoped request authentication;
- backend `agent.install` authorization;
- configurable enrollment name;
- configurable supported agent type;
- configurable token TTL;
- one-time raw enrollment token presentation.

## Enrollment contract

The frontend sends the existing backend fields:

- `name`;
- `agent_type`;
- `ttl_minutes`.

Existing backend constraints are preserved:

- name length: 1 through 160 characters;
- agent type pattern: `[a-z0-9_-]{2,32}`;
- default agent type: `linux`;
- TTL range: 5 through 1440 minutes;
- default TTL: 30 minutes.

## Credential handling

The raw enrollment token is returned by the backend only when created.

The frontend keeps the raw credential only in React page state.

It is not written to:

- localStorage;
- sessionStorage;
- URL parameters;
- application logs.

The operator must save the token before dismissing it or leaving the page.

## Backend behavior

Existing backend behavior remains authoritative:

- raw enrollment tokens are generated server-side;
- only the token hash is stored;
- expiration is enforced server-side;
- enrollment tokens are single-use;
- successful enrollment consumes the token;
- token creation is audit logged as
  `agent.enrollment_token.create`.

## Existing agent controls

Existing agent operations remain unchanged:

- live heartbeat telemetry;
- token lifecycle diagnostics;
- lifecycle alerts;
- administrator token rotation;
- agent revocation;
- inventory submission and display;
- agent task execution lifecycle.

## Safety and authorization

The frontend does not bypass backend authorization.

Token creation requires the existing `agent.install` permission.

No enrollment-token listing, revocation, reuse, extension or recovery
capability is invented because those capabilities are not exposed by the
current API contract.

## Backend and schema impact

- backend functional delta: none;
- Alembic delta: none;
- dependency delta: none;
- runtime topology: unchanged;
- Alembic head remains `0021_worker_operational_state`.

## Frontend impact

Changed functional files:

- `apps/web/src/api/agents.ts`;
- `apps/web/src/pages/Agents.tsx`.

No CSS changes are required.

## Validation

Release validation requires:

- enrollment API client contract;
- existing backend enrollment route validation;
- `agent.install` permission contract;
- raw-token state-only handling;
- no token persistence;
- no backend functional delta;
- no Alembic delta;
- no dependency delta;
- Web ESLint;
- Web TypeScript/Vite production build;
- API regression suite;
- release metadata verification;
- `git diff --check`.

## Release identity

- API version: `0.3.14-alpha`
- Python package version: `0.3.14a0`
