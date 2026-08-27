# Public Control Center

The public AI-project SRV Control Center is available at:

- https://ai-project-srv-control.kirik20406.chatgpt.site

## Purpose

This public site presents the approved dark Control Center design direction and
the operating model of AI-project SRV. It is a public-facing interface shell,
not an authenticated production console.

## Source-of-truth boundary

- The `OTBuHTa/AI-project-SRV` repository and its API contracts remain the
  source of truth.
- The public site must not expose credentials, private infrastructure addresses,
  workspace data, or privileged actions.
- Values shown on the public site are representative UI states unless they are
  connected to an explicitly public, read-only endpoint.
- Authentication, workspace isolation, policy evaluation, approvals, audit
  logging, and agent capability controls remain owned by the application.

## Integration path

1. Reuse the visual system in `apps/web` without replacing the existing React,
   routing, authentication, query, or realtime architecture.
2. Bind each UI surface only to an implemented backend endpoint and permission
   contract.
3. Prioritize the Infrastructure Control Center vertical slice, then Dashboard
   and shared navigation.
4. Keep public presentation and authenticated operations separate.
5. Validate frontend lint/build and review the integration through a draft PR.

## Public deployment

The public Site is independently deployable and intentionally contains no
secrets or direct access to the private AI-project SRV infrastructure.
