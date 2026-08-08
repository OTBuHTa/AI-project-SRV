from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityPolicy:
    risk_level: int
    requires_approval: bool
    allowed: bool = True


CAPABILITY_POLICIES = {
    "docker.container.restart": CapabilityPolicy(risk_level=2, requires_approval=True),
}


def get_capability_policy(capability: str) -> CapabilityPolicy:
    return CAPABILITY_POLICIES.get(capability, CapabilityPolicy(5, True, False))
