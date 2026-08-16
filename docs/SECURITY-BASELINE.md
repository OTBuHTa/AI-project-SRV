# Security baseline — v0.1.26-alpha

Before exposing AI-project SRV outside the LAN, production configuration must
satisfy the following baseline.

## Production startup policy

When:

`APP_ENV=production`

the API refuses to start unless:

- `JWT_SECRET` is non-empty and is not the development default;
- `BOOTSTRAP_ENABLED=false`;
- `METRICS_BEARER_TOKEN` is configured;
- `SECURE_HEADERS_HSTS_ENABLED=true`;
- `AUTH_RATE_LIMIT_ENABLED=true`;
- `FORWARDED_ALLOW_IPS` explicitly identifies trusted proxy addresses or
  networks;
- `FORWARDED_ALLOW_IPS` does not contain `*`.

## Transport security

Terminate TLS at a controlled reverse proxy.

Do not expose the API over plaintext Internet HTTP.

Production enables:

`Strict-Transport-Security: max-age=31536000; includeSubDomains`

Additional HTTP response headers include:

- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: no-referrer`;
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`.

## Authentication

Access tokens use short-lived JWTs.

Refresh tokens are cryptographically random and stored only as hashes.

Successful authentication token responses use:

- `Cache-Control: no-store`;
- `Pragma: no-cache`.

Login abuse protection uses Redis-backed counters scoped to:

- source IP;
- normalized account identity.

Raw account identifiers and source IPs are hashed before they are used in Redis
rate-limit keys.

Authentication rate limiting fails closed when Redis is unavailable.

## Metrics

`GET /metrics` supports bearer-token protection.

Production requires `METRICS_BEARER_TOKEN`.

Prometheus metric labels remain intentionally low-cardinality and must not
contain:

- workspace IDs;
- user IDs;
- agent IDs;
- destination IDs;
- endpoints;
- access tokens;
- refresh tokens;
- agent tokens;
- credentials.

## Reverse proxy trust boundary

Client IP semantics are delegated to Uvicorn proxy-header handling.

Forwarded headers are accepted only from addresses configured through:

`FORWARDED_ALLOW_IPS`

Never configure:

`FORWARDED_ALLOW_IPS=*`

for an Internet-reachable deployment.

Application authorization, audit and rate-limit logic use the resolved
`request.client.host`.

## Operational error handling

Public API responses must use stable error codes rather than raw exception
messages.

Notification endpoint policy failures return:

`invalid_notification_endpoint`

Backup storage probe failures return:

`backup_storage_unavailable`

Raw operating-system, transport, connection, endpoint or secret-bearing
exception strings must not be returned to API clients.

## Infrastructure isolation

PostgreSQL and Redis must remain restricted to the internal service network and
must not be directly Internet accessible.

NAS remains backup/storage infrastructure only.

## Authorization and mutation

Infrastructure APIs use workspace-scoped permissions.

Do not expose a generic root shell as an AI capability.

Agents publish narrow typed capabilities.

Mutating operations remain governed by:

- capability constraints;
- Policy Engine authorization;
- explicit approval where required;
- audit;
- execution verification.

The LLM is advisory.

The Policy Engine remains authoritative.

## Backup security

Back up PostgreSQL and required configuration to the backup storage tier.

Restore verification must be tested regularly.

Backup storage health degradation remains operational state and does not change
the infrastructure readiness contract.

## Current limitations

Administrator MFA is not yet enforced by this release and remains required
before broad external-user production deployment.
