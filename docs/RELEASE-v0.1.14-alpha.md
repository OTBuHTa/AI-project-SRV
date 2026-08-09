# AI-project SRV v0.1.14-alpha

## Notification Security Hardening

This release hardens the notification delivery subsystem introduced
in v0.1.12-alpha and expanded with workspace routing in
v0.1.13-alpha.

## Highlights

### Webhook endpoint policy

Notification destinations now pass an explicit outbound endpoint
policy.

The policy:

- accepts only HTTP and HTTPS;
- rejects URL credentials and fragments;
- rejects loopback, link-local, multicast, unspecified, and reserved
  addresses;
- rejects private addresses by default;
- resolves hostnames and validates resolved addresses;
- runs at both API configuration time and worker execution time.

Private-network endpoints can be enabled explicitly for self-hosted
deployments with:

`notification_webhook_allow_private_networks=true`

### Signed webhook delivery

Webhook delivery supports HMAC-SHA256 authentication.

When a signing secret is configured:

`notification_webhook_signing_secret=<secret>`

requests include:

- `X-AI-SRV-Timestamp`
- `X-AI-SRV-Signature`

The signature is generated from the exact raw JSON bytes transmitted
to the receiver.

Unsigned delivery remains available when no signing secret is
configured.

### Terminal delivery cancellation

Notification deliveries now distinguish permanent configuration
failures from transient transport failures.

Permanent conditions become:

`canceled`

Examples:

- destination deleted;
- destination disabled;
- unsupported destination channel.

Canceled deliveries have no future retry time and are not reclaimed
by the delivery queue.

Transient failures continue to use:

- `failed`;
- exponential backoff;
- maximum attempt limits.

## Security Model

Notification delivery remains separate from infrastructure
remediation.

An alert or webhook delivery does not authorize infrastructure
changes.

The architecture continues to enforce:

**LLM advisory, Policy Engine authoritative.**

## Compatibility

No database migration is required for the new canceled state because
the existing delivery status column is not database-enum constrained.

Existing notification routing and historical delivery records remain
compatible.

## Verification

Validated on the v0.1.14-alpha branch:

- webhook endpoint-policy unit tests;
- API unsafe-endpoint rejection;
- worker runtime SSRF protection;
- HMAC signature tests;
- signed and unsigned transport tests;
- terminal delivery cancellation tests;
- retry/backoff regression tests.

Full test suite:

`100 passed, 1 warning`

The remaining warning is the known Starlette TestClient/httpx
deprecation warning.
