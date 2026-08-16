# AI-project SRV v0.1.26-alpha

## Production Security Hardening

v0.1.26-alpha strengthens the production security boundary of the API without
changing the established infrastructure readiness semantics.

## Protected Prometheus endpoint

`GET /metrics` now supports bearer authentication.

Production requires:

`METRICS_BEARER_TOKEN`

Missing or invalid metrics credentials return `401`.

## Production startup security policy

When:

`APP_ENV=production`

the API refuses to start unless:

- the JWT secret is non-default;
- bootstrap is disabled;
- the metrics bearer token is configured;
- HSTS is enabled;
- Redis-backed login rate limiting is enabled;
- trusted reverse-proxy addresses are explicitly configured;
- wildcard proxy trust is not used.

## HTTP security headers

Responses now include:

- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: no-referrer`;
- restricted `Permissions-Policy`.

Production additionally requires:

`Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Authentication cache protection

Successful:

- bootstrap;
- login;
- refresh

responses send:

- `Cache-Control: no-store`;
- `Pragma: no-cache`.

## Login abuse protection

Login protection is backed by Redis.

Limits apply independently to:

- source IP;
- normalized account.

Raw IP addresses and account identifiers are not stored in Redis key names.

Production requires the limiter to be enabled.

Limiter Redis failures fail authentication closed.

## Reverse proxy trust boundary

Forwarded client addresses are handled by Uvicorn.

Trusted proxies are configured through:

`FORWARDED_ALLOW_IPS`

Production rejects wildcard trust.

Regression coverage verifies that an untrusted peer cannot spoof
`X-Forwarded-For`.

## Error response hardening

Known operational exception leaks were removed.

Notification endpoint policy failures now return:

`invalid_notification_endpoint`

Backup storage probe failures return:

`backup_storage_unavailable`

Regression tests verify that injected secret-bearing exception strings are not
returned to callers.

## Readiness

`/ready` is unchanged.

Infrastructure readiness continues to depend only on:

- PostgreSQL;
- Redis.

Operational or business degradation does not change readiness.

## Database

No database migration is included.

Current Alembic head remains:

`0021_worker_operational_state`

## Operational boundaries

This release does not:

- introduce automatic remediation;
- grant the LLM direct infrastructure authority;
- expose a universal root shell;
- change approval semantics for mutating capabilities.

**LLM advisory, Policy Engine authoritative.**

## Validation scope

Release validation includes:

- production startup-policy tests;
- metrics authentication tests;
- HTTP security-header tests;
- HSTS tests;
- authentication cache-control tests;
- Redis login rate-limit unit tests;
- login rate-limit API tests;
- reverse-proxy trust tests;
- notification endpoint leakage regression tests;
- backup storage leakage regression tests;
- full API regression;
- Python compilation;
- `git diff --check`;
- production-safe runtime validation.
