import {
  apiJson,
  workspaceHeaders,
} from './http'

export type MikroTikDhcpClient = {
  interface?: string
  status?: string
  address?: string
  gateway?: string
}

export type MikroTikStatus = {
  connected: boolean
  identity?: string
  version?: string
  uptime?: string
  cpu_load?: string
  free_memory?: string
  default_route_present: boolean
  dhcp_clients: MikroTikDhcpClient[]
  interface_count: number
  address_count: number
  wan_interface: string
  wan_running: boolean
  wan_dhcp_bound: boolean
  wan_address?: string | null
  expected_wan_ip?: string | null
  wan_ip_matches_expected?: boolean | null
}

export type MikroTikSnapshot = {
  identity: Record<string, string>
  resource: Record<string, string>
  interfaces: Array<Record<string, string>>
  addresses: Array<Record<string, string>>
  routes: Array<Record<string, string>>
  dhcp_clients: Array<Record<string, string>>
  dns: Record<string, string>
}

export function getMikroTikStatus(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<MikroTikStatus>(
    '/api/v1/mikrotik/status',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function getMikroTikSnapshot(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<MikroTikSnapshot>(
    '/api/v1/mikrotik/snapshot',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}

export function renewMikroTikDhcp(
  accessToken: string,
  workspaceId: string,
  interfaceName: string,
) {
  return apiJson<{
    action: string
    interface: string
    status: string
  }>(
    '/api/v1/mikrotik/actions/dhcp-renew',
    {
      method: 'POST',
      headers: {
        ...workspaceHeaders(
          accessToken,
          workspaceId,
        ),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        interface: interfaceName,
      }),
    },
  )
}
