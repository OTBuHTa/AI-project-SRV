# Release v0.1.5-alpha

## Added
- AI-originated, policy-controlled ActionPlan proposals.
- Deterministic mapping to `docker.container.restart` only.
- Explicit approval retained for all write operations.
- Post-execution `verifying` state.
- Fresh-heartbeat verification of Docker container state.
- Verification audit events and persisted verification evidence.
- Alembic revision `0006_ai_action_verification`.

## Security invariant
The LLM is advisory. It cannot produce arbitrary executable commands or bypass capability policy, approval, agent allowlists, or verification.
