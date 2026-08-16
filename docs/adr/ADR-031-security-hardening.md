# ADR-031: Production Security Hardening

## Status

Accepted for v0.1.26-alpha.

## Context

AI-project SRV already provides workspace authorization, token lifecycle
controls, notification endpoint policy, audit mechanisms and production
observability.

Before broader production exposure, several controls must become explicit and
fail-safe:

- `/metrics` authentication;
- unsafe production configuration rejection;
- browser-facing security headers;
- HSTS;
- authentication response cache prevention;
- login abuse protection;
- trusted reverse-proxy boundaries;
- sanitization of operational error responses.

Security controls must not change the established readiness contract.

## Decision

Introduce a production security policy enforced during API startup and add
defense-in-depth controls at the HTTP, authentication, observability and proxy
boundaries.

## Production startup validation

When `APP_ENV=production`, startup fails when any of the following is unsafe:

- default or empty JWT secret;
- bootstrap remains enabled;
- metrics bearer token is absent;
- HSTS is disabled;
- authentication rate limiting is disabled;
- trusted proxy configuration is empty;
- trusted proxy configuration contains the wildcard `*`.

Development remains backward compatible.

## Metrics protection

`GET /metrics` accepts a bearer token when
`METRICS_BEARER_TOKEN` is configured.

Token comparison uses constant-time comparison semantics.

Missing or invalid credentials return `401`.

Production requires metrics authentication.

## HTTP security headers

Responses include:

- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: no-referrer`;
- restricted `Permissions-Policy`.

When enabled, HSTS is:

`max-age=31536000; includeSubDomains`

Production requires HSTS.

## Sensitive response caching

Successful bootstrap, login and refresh responses include:

- `Cache-Control: no-store`;
- `Pragma: no-cache`.

The policy is restricted to sensitive authentication responses rather than
globally disabling HTTP caching.

## Login abuse protection

Failed login attempts are tracked in Redis using both:

- source-IP scope;
- normalized-account scope.

Redis keys contain SHA-256 fingerprints instead of raw IP addresses or account
identifiers.

Rate-limit state uses bounded expiry windows.

When protection is enabled, Redis failures fail authentication closed rather
than silently bypassing the limiter.

Production requires rate limiting.

## Trusted proxy boundary

The application does not implement a second custom forwarded-header parser.

Uvicorn remains responsible for `X-Forwarded-For` processing.

Forwarded headers are trusted only from addresses or CIDR networks configured
through:

`FORWARDED_ALLOW_IPS`

Wildcard trust is prohibited in production.

Application code continues to consume resolved `request.client.host`.

## Operational error sanitization

Raw policy and operating-system exception strings are not returned to API
clients.

Notification endpoint validation exposes the stable public error:

`invalid_notification_endpoint`

Backup storage probe failures expose:

`backup_storage_unavailable`

Internal exception chaining remains available for server-side diagnostics where
appropriate.

## Readiness boundary

`/ready` remains unchanged.

Readiness continues to depend only on:

- PostgreSQL;
- Redis.

Security-related operational degradation does not redefine readiness semantics.

## Consequences

### Positive

- production fails fast on unsafe security configuration;
- metrics are protected in production;
- browser and transport security posture is stronger;
- authentication tokens are protected from response caching;
- brute-force resistance is persistent and distributed through Redis;
- arbitrary clients cannot spoof forwarded client addresses;
- known raw exception leaks are removed.

### Tradeoffs

- production deployments require explicit security environment configuration;
- Redis availability becomes part of login availability when rate limiting is
  enabled;
- reverse-proxy addressing must be known and maintained accurately;
- HSTS requires correct HTTPS deployment before production startup.

## Database

No new database migration is introduced.

Alembic head remains:

`0021_worker_operational_state`
