# ADR-010 — ActionPlan, Policy Engine and Approval

## Decision
All infrastructure mutations are represented as durable ActionPlans. Unknown capabilities are denied by default. v0.1.4-alpha enables only `docker.container.restart`, risk level 2, with explicit approval.

## Security invariants
- LLM cannot execute an action directly.
- Capability and parameters are validated server-side.
- Container must exist in the agent's last reported Docker inventory.
- Approval is recorded with user identity and timestamp.
- Agent receives a structured task, never arbitrary shell text.
- Linux Agent uses an argv subprocess call and never `shell=True` / `sh -c`.
- Result is persisted and appended to the tamper-evident AuditLog.
