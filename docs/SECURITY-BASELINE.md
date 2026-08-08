# Security baseline — v0.1.0-alpha

Before exposing AI-project SRV outside the LAN:

1. Set a strong unique `JWT_SECRET` and disable `BOOTSTRAP_ENABLED` after first initialization.
2. Terminate TLS at the reverse proxy; never expose the API over plaintext Internet HTTP.
3. Restrict the database and Redis to the internal Docker network.
4. Enable administrator MFA before onboarding external users (planned next security iteration).
5. Use workspace-scoped permissions on every infrastructure endpoint.
6. Never expose a generic root shell as an AI tool. Agents publish narrow typed capabilities.
7. Require approval for mutating capabilities and record request, approval, execution and verification in audit.
8. Back up PostgreSQL and configuration to NAS and test restoration regularly.
