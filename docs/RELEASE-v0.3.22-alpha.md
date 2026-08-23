# AI-project SRV v0.3.22-alpha

## Summary

Introduces the operational automation layer for AI-project SRV.

## Added

- `tools/srvctl` operational CLI.
- Machine-readable JSON output.
- Environment and runtime doctor checks.
- API and frontend CI aggregation.
- Safe autopilot validation.
- Production readiness gate.
- Guarded deploy planning and execution.
- Deployment state persistence.
- Rollback planning.
- Guarded rollback executor using the previous Git revision.
- Release acceptance gate.

## Safety

- Deployment is refused outside a clean `main`.
- `HEAD` must match `origin/main`.
- Production readiness remains fail-closed while the runtime environment is `development`.
- Rollback execution requires an explicit failed deployment state.
- Rollback uses a detached temporary Git worktree and removes it after execution.
- Infrastructure mutations remain constrained by existing project policy and approval contracts.

## Validation

- API targeted WebSocket authorization tests.
- Full API regression suite.
- Frontend lint and production build.
- Docker Compose configuration validation.
- `git diff --check`.
- `srvctl autopilot`.
- `srvctl release-gate`.

## Migration impact

No Alembic migration is introduced by this release.

## Dependency impact

No runtime dependency is added by this release.
