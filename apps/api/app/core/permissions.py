from app.models.core import Role

ROLE_PERMISSIONS: dict[str, set[str]] = {
    Role.PLATFORM_OWNER.value: {"*"},
    Role.PLATFORM_ADMIN.value: {
        "workspace.read", "resource.read", "resource.connect", "agent.read", "agent.install",
        "agent.update", "agent.revoke", "mcp.read", "audit.read",
    },
    Role.ORGANIZATION_OWNER.value: {"*"},
    Role.ORGANIZATION_ADMIN.value: {
        "workspace.read", "workspace.manage", "resource.read", "resource.connect",
        "resource.execute", "agent.read", "agent.install", "agent.update", "agent.revoke",
        "mcp.read", "mcp.install", "mcp.execute", "workflow.read", "workflow.create",
        "workflow.execute", "workflow.approve", "action.read", "action.create", "action.approve", "audit.read", "billing.read",
    },
    Role.OPERATOR.value: {
        "workspace.read", "resource.read", "resource.execute", "agent.read",
        "workflow.read", "workflow.execute", "action.read", "action.create", "action.approve",
    },
    Role.ANALYST.value: {"workspace.read", "resource.read", "agent.read", "workflow.read", "action.read", "audit.read"},
    Role.VIEWER.value: {"workspace.read", "resource.read", "agent.read", "workflow.read", "action.read"},
    Role.DEVELOPER.value: {
        "workspace.read", "resource.read", "agent.read", "agent.install", "mcp.read",
        "mcp.install", "mcp.execute", "workflow.read", "workflow.create",
    },
    Role.BILLING_MANAGER.value: {"workspace.read", "billing.read", "billing.manage"},
}


def has_permission(role: str, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(role, set())
    return "*" in permissions or permission in permissions
