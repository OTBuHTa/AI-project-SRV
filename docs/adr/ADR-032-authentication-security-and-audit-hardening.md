# ADR-032: Authentication Security and Audit Hardening

## Status

Accepted for v0.1.27-alpha.

## Context

v0.1.26-alpha introduced Redis-backed login abuse protection using independent
source-IP and normalized-account counters.

The initial implementation cleared both counters after a successful login.

That behavior weakened the shared source-IP protection boundary because a valid
login from the same source could remove accumulated IP-level brute-force
pressure.

Rate-limit denial and Redis fail-closed paths also did not persist dedicated
authentication audit events.

Existing denied-login audit records stored the normalized email address in
audit details.

Authentication security telemetry must remain useful for incident correlation
without unnecessarily persisting raw account identifiers.

The repository also had no automated GitHub Actions validation for pushes and
pull requests.

## Decision

Harden login rate-limit state management, security audit coverage, audit
identity minimization, and repository CI validation.

## Source-IP rate-limit preservation

A successful login clears only the normalized-account failure counter.

The source-IP counter is not deleted by a successful login.

It remains subject to its configured Redis expiry window.

This preserves source-level brute-force pressure independently from valid
account authentication.

## Authentication security audit events

Rate-limit security outcomes are recorded using the existing `auth.login`
audit action.

The following paths are explicitly audited:

- precheck rate-limit denial;
- Redis failure during rate-limit precheck;
- Redis failure while recording a failed login;
- Redis failure while clearing account failures after successful credentials.

Audit records include bounded categorical fields:

- `reason`;
- `stage`.

Rate-limit Redis failures continue to fail authentication closed.

## Audit identity minimization

Denied and security-related login audit events do not store a raw email address
in `details`.

Instead, they store:

`account_fingerprint`

The fingerprint is SHA-256 over the normalized account identifier:

- surrounding whitespace removed;
- lowercase normalization applied.

The same normalized fingerprint semantics are used for Redis account-scoped
rate-limit keys.

This provides stable correlation without placing the raw account identifier in
the audit details payload.

Successful login audit events continue to use the authenticated user
`actor_id`.

## Invalid credential audit semantics

Ordinary invalid-credential failures use the same privacy contract.

Their audit details contain:

- `account_fingerprint`;
- `reason=invalid_credentials`;
- `stage=credentials`.

Raw passwords are never stored in audit events.

## Source address

Authentication audit events use the resolved request source address provided by
the existing trusted-proxy boundary.

No new forwarded-header parser is introduced.

## CI baseline

Add a GitHub Actions workflow for API validation on:

- pushes to `main`;
- pushes to `agent/**`;
- pull requests targeting `main`.

The workflow uses Python 3.12 and performs:

- editable installation with development dependencies;
- Python source compilation;
- the full API pytest suite;
- `git diff --check`.

The current test suite does not require dedicated PostgreSQL or Redis service
containers because relevant external dependencies are mocked or isolated in
tests.

## Readiness boundary

`/ready` is unchanged.

Readiness continues to depend only on:

- PostgreSQL;
- Redis.

Authentication denials, rate-limit pressure, audit outcomes, and CI state do
not redefine runtime readiness semantics.

## Operational boundaries

This release does not:

- introduce automatic remediation;
- grant the LLM infrastructure authority;
- expose a universal root shell;
- change capability approval semantics;
- change token lifetime policy;
- change workspace authorization semantics.

**LLM advisory, Policy Engine authoritative.**

## Consequences

### Positive

- successful authentication can no longer erase shared source-IP brute-force
  pressure;
- rate-limit denial and fail-closed paths become auditable;
- denied-login audit records no longer persist raw account identifiers;
- account correlation remains stable through deterministic fingerprints;
- local validation is mirrored by automated GitHub pull-request checks.

### Tradeoffs

- successful login no longer resets source-IP pressure, so heavily abused shared
  source addresses remain constrained until the IP counter expires;
- SHA-256 account fingerprints are pseudonymous correlation identifiers, not
  anonymous data;
- authentication availability remains dependent on Redis when production rate
  limiting is enabled;
- CI dependency installation depends on the public Python package ecosystem.

## Database

No database migration is introduced.

Alembic head remains:

`0021_worker_operational_state`
