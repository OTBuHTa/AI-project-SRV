# AI-project SRV v0.1.27-alpha

## Authentication Security & Audit Hardening

v0.1.27-alpha strengthens login abuse protection, improves authentication audit
coverage, minimizes account identity data in denied-login audit events, and
introduces automated API CI validation.

## Login rate-limit hardening

Successful authentication now clears only the account-specific failure counter.

The source-IP failure counter is preserved until its configured Redis expiry.

This prevents a valid login from resetting accumulated brute-force pressure for
other attempts originating from the same source address.

## Rate-limit security auditing

Authentication audit coverage now includes:

- `429` rate-limit denial during login precheck;
- Redis fail-closed `503` during rate-limit precheck;
- Redis fail-closed `503` while recording failed-login state;
- Redis fail-closed `503` while clearing successful account failure state.

These events use stable reason and stage classifications.

## Authentication audit privacy

Denied and security-related login audit events no longer store raw email
addresses in audit details.

They use a SHA-256:

`account_fingerprint`

derived from the normalized account identifier.

Normalization is shared with account-scoped rate-limit state.

Ordinary `401 invalid_credentials` audit events follow the same privacy
contract.

Successful login events continue to identify the authenticated principal through
`actor_id`.

## Source-IP protection

Login abuse protection continues to maintain independent scopes for:

- source IP;
- normalized account.

Only account-scoped state is cleared after successful authentication.

Rate-limit Redis failures continue to fail login closed.

## Continuous integration

The repository now contains a GitHub Actions API validation workflow.

It runs on:

- pushes to `main`;
- pushes to `agent/**`;
- pull requests targeting `main`.

Validation includes:

- Python 3.12 environment setup;
- development dependency installation;
- Python compilation;
- the full API pytest suite;
- `git diff --check`.

No PostgreSQL or Redis CI service containers are required by the current test
suite.

## Readiness

`/ready` is unchanged.

Infrastructure readiness continues to depend only on:

- PostgreSQL;
- Redis.

Authentication security events do not change readiness semantics.

## Database

No database migration is included.

Current Alembic head remains:

`0021_worker_operational_state`

## Operational boundaries

This release does not:

- introduce automatic remediation;
- grant the LLM direct infrastructure authority;
- expose a universal root shell;
- change approval semantics for mutating capabilities;
- change workspace authorization semantics.

**LLM advisory, Policy Engine authoritative.**

## Validation scope

Release validation includes:

- source-IP and account rate-limit unit tests;
- successful-login rate-limit reset regression;
- `429` rate-limit audit regression;
- Redis fail-closed audit regressions;
- invalid-credential audit privacy regression;
- account fingerprint normalization regression;
- authentication cache-control regression;
- full API regression;
- Python compilation;
- `git diff --check`;
- GitHub Actions API CI.
