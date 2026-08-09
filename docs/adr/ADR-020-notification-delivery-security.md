# ADR-020: Notification Delivery Security and Terminal Delivery States

## Status

Accepted

## Context

AI-project SRV v0.1.13-alpha introduced workspace-scoped
notification destinations and routes.

Webhook destinations can cause the control plane to make outbound
HTTP requests. This introduces security and reliability concerns:

- server-side request forgery through arbitrary webhook endpoints;
- delivery authenticity for webhook receivers;
- retry loops for permanently invalid delivery configurations;
- distinction between transient transport failures and terminal
  destination failures.

The notification subsystem must remain operational messaging only.
Notification state must not grant remediation authority.

The existing architectural rule remains:

**LLM advisory, Policy Engine authoritative.**

## Decision

### Endpoint policy

Webhook endpoints are validated before persistence through the API
and again immediately before transport execution.

The policy:

- permits only HTTP and HTTPS;
- requires a hostname;
- rejects URL userinfo;
- rejects URL fragments;
- rejects loopback addresses;
- rejects link-local addresses;
- rejects multicast addresses;
- rejects unspecified addresses;
- rejects reserved addresses;
- rejects private addresses by default;
- resolves hostnames and validates all resolved addresses.

Private-network webhook endpoints may be enabled explicitly with:

`notification_webhook_allow_private_networks=true`

This exception exists because AI-project SRV is designed for
self-hosted infrastructure where internal webhook receivers may be
legitimate.

Runtime validation remains mandatory even when the destination was
validated during API creation or update. This protects against stale
records, direct database writes, and older persisted data.

### Webhook signing

Webhook payloads use deterministic JSON serialization.

When `notification_webhook_signing_secret` is configured, each
request includes:

- `X-AI-SRV-Timestamp`
- `X-AI-SRV-Signature`

The signature is:

`HMAC-SHA256(secret, timestamp + "." + raw_body)`

The signature is calculated from the exact bytes transmitted to the
receiver.

An empty signing secret preserves unsigned delivery behavior for
backward compatibility.

### Terminal delivery state

A new logical delivery state is introduced:

`canceled`

No database migration is required because delivery status is stored
as an unconstrained string field.

Canceled deliveries have:

- `status = canceled`;
- `next_attempt_at = NULL`;
- a terminal reason stored in `last_error`.

The queue claim query only claims pending, failed, or stale sending
deliveries. Therefore canceled deliveries are terminal and are not
retried.

The worker cancels delivery when:

- the destination no longer exists;
- the destination is disabled;
- the configured notification channel is unsupported.

Transient failures remain retryable:

- network failures;
- HTTP transport errors;
- endpoint-policy failures encountered during execution.

Transient failures continue using the existing exponential backoff
and maximum-attempt rules.

## Security Properties

The endpoint policy reduces SSRF risk but does not replace network
egress controls.

Operators should still apply:

- host firewall policy;
- container network segmentation;
- outbound proxy policy where appropriate;
- restricted workspace management permissions.

Allowing private-network endpoints intentionally expands the
destination trust boundary and should only be enabled in controlled
self-hosted environments.

Webhook signing authenticates messages to receivers but does not
encrypt the payload. HTTPS remains recommended.

Receivers should validate both signature and timestamp and reject
stale timestamps to reduce replay risk.

## Consequences

### Positive

- webhook destinations are validated at API and execution boundaries;
- cloud metadata and loopback targets are blocked by default;
- internal destinations remain possible through explicit operator
  configuration;
- webhook receivers can authenticate AI-project SRV deliveries;
- permanent destination failures no longer consume retry capacity;
- transient transport failures retain retry behavior;
- no schema migration is required for the canceled state.

### Tradeoffs

- DNS resolution during endpoint validation adds network dependency;
- DNS rebinding remains a broader concern and may require transport-
  level DNS pinning or controlled egress in future releases;
- signing secrets are currently global rather than destination-
  scoped;
- secrets are not yet stored through an encrypted destination-secret
  facility;
- endpoint validation cannot replace infrastructure-level egress
  restrictions.

## Verification

The implementation is verified by unit and regression tests covering:

- supported and unsupported URL schemes;
- special-use and private IP rejection;
- explicit private-network allowance;
- DNS resolution to private addresses;
- API-side unsafe destination rejection;
- worker-side endpoint revalidation;
- deterministic HMAC generation;
- signed and unsigned webhook transport;
- signing-secret propagation through the worker;
- terminal canceled delivery behavior;
- missing destination cancellation;
- disabled destination cancellation;
- unsupported-channel cancellation;
- existing retry/backoff behavior.

Full regression result:

`100 passed, 1 warning`

The warning is the existing Starlette TestClient deprecation warning
and is unrelated to this ADR.
