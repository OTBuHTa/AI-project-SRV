const ROLE_PERMISSIONS: Record<
  string,
  readonly string[]
> = {
  platform_owner: ['*'],

  platform_admin: [
    'workspace.read',
    'resource.read',
    'resource.connect',
    'agent.read',
    'agent.install',
    'agent.update',
    'agent.revoke',
    'mcp.read',
    'audit.read',
    'network.read',
  ],

  organization_owner: ['*'],

  organization_admin: [
    'workspace.read',
    'workspace.manage',
    'resource.read',
    'resource.connect',
    'resource.execute',
    'agent.read',
    'agent.install',
    'agent.update',
    'agent.revoke',
    'mcp.read',
    'mcp.install',
    'mcp.execute',
    'workflow.read',
    'workflow.create',
    'workflow.execute',
    'workflow.approve',
    'action.read',
    'action.create',
    'action.approve',
    'audit.read',
    'billing.read',
    'network.read',
    'network.execute',
  ],

  operator: [
    'workspace.read',
    'resource.read',
    'resource.execute',
    'agent.read',
    'workflow.read',
    'workflow.execute',
    'action.read',
    'action.create',
    'action.approve',
    'network.read',
    'network.execute',
  ],

  analyst: [
    'workspace.read',
    'resource.read',
    'agent.read',
    'workflow.read',
    'action.read',
    'audit.read',
    'network.read',
  ],

  viewer: [
    'workspace.read',
    'resource.read',
    'agent.read',
    'workflow.read',
    'action.read',
    'network.read',
  ],

  developer: [
    'workspace.read',
    'resource.read',
    'agent.read',
    'agent.install',
    'mcp.read',
    'mcp.install',
    'mcp.execute',
    'workflow.read',
    'workflow.create',
    'network.read',
  ],

  billing_manager: [
    'workspace.read',
    'billing.read',
    'billing.manage',
  ],
}

export function hasPermission(
  role: string | null | undefined,
  permission: string,
) {
  if (!role) {
    return false
  }

  const permissions =
    ROLE_PERMISSIONS[role]

  if (!permissions) {
    return false
  }

  return permissions.includes('*')
    || permissions.includes(permission)
}
