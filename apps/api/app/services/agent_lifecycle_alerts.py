from dataclasses import dataclass


@dataclass(frozen=True)
class AgentLifecycleAlert:
    severity: str
    code: str
    message: str


def evaluate_agent_lifecycle_alerts(
    diagnostics: dict,
) -> list[AgentLifecycleAlert]:
    alerts: list[AgentLifecycleAlert] = []

    expired = int(
        diagnostics.get("expired_pending_rotations", 0)
    )
    incomplete = int(
        diagnostics.get("incomplete_pending_rotations", 0)
    )
    revoked_pending = int(
        diagnostics.get("revoked_with_pending_rotation", 0)
    )

    if expired > 0:
        alerts.append(
            AgentLifecycleAlert(
                severity="warning",
                code="agent_token_rotation_expired",
                message=(
                    f"{expired} expired agent token rotation(s) "
                    "require lifecycle cleanup."
                ),
            )
        )

    if incomplete > 0:
        alerts.append(
            AgentLifecycleAlert(
                severity="critical",
                code="agent_token_rotation_incomplete",
                message=(
                    f"{incomplete} agent token rotation(s) "
                    "have incomplete pending state."
                ),
            )
        )

    if revoked_pending > 0:
        alerts.append(
            AgentLifecycleAlert(
                severity="critical",
                code="agent_revoked_pending_rotation",
                message=(
                    f"{revoked_pending} revoked agent(s) retain "
                    "pending token rotation state."
                ),
            )
        )

    return alerts
