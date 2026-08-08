# ADR-007: Agent identity and enrollment

## Decision
Agents initiate outbound HTTPS connections and enroll with a short-lived, single-use enrollment token. Successful enrollment returns a high-entropy opaque agent credential. Only its SHA-256 hash is stored server-side.

## Current alpha boundary
`v0.1.1-alpha` uses bearer agent credentials over TLS. Before Internet-facing production use, replace this transport identity with per-agent mTLS certificates or workload identity while preserving the enrollment workflow.

## Security properties
- no inbound port required on managed hosts;
- enrollment token is single-use and expires;
- agent credential can be revoked independently;
- agent exposes an allowlisted capability set;
- initial Linux agent is read-only and has no generic shell capability.
