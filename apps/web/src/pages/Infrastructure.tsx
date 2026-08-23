import {
  Activity,
  Boxes,
  CheckCircle2,
  Cpu,
  Network,
  RefreshCcw,
  Router,
  Server,
  TriangleAlert,
} from 'lucide-react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  getAgents,
  type Agent,
} from '../api/agents'
import {
  getMikroTikSnapshot,
  getMikroTikStatus,
  renewMikroTikDhcp,
} from '../api/mikrotik'
import { useAuth } from '../auth/useAuth'
import { hasPermission } from '../auth/permissions'
import { useWorkspaceTelemetry } from '../realtime/useWorkspaceTelemetry'

function percent(
  value: number | undefined,
) {
  return typeof value === 'number'
    ? `${Math.round(value)}%`
    : '—'
}

function formatDate(
  value: string | null,
) {
  if (!value) {
    return '—'
  }

  return new Date(value).toLocaleString()
}

function LinuxHostCard({
  agent,
}: {
  agent: Agent
}) {
  const online =
    agent.status === 'online'
    || agent.status === 'healthy'

  const docker =
    agent.metrics?.docker

  const dockerValue =
    docker?.available === false
      ? 'unavailable'
      : typeof docker?.containers_running
        === 'number'
        ? `${docker.containers_running} / ${
            docker.containers_total ?? '—'
          }`
        : '—'

  return (
    <article className="resource-card">
      <header className="resource-card__header">
        <div className="agent-title">
          <Server size={20} />

          <div>
            <strong>
              {agent.hostname}
            </strong>
            <small>
              {agent.agent_type}
              {' · '}
              {agent.version}
            </small>
          </div>
        </div>

        {online ? (
          <CheckCircle2 size={19} />
        ) : (
          <TriangleAlert size={19} />
        )}
      </header>

      <div className="resource-stats">
        <div>
          <Cpu size={17} />
          <span>CPU</span>
          <strong>
            {percent(
              agent.metrics?.cpu_percent,
            )}
          </strong>
        </div>

        <div>
          <Activity size={17} />
          <span>Memory</span>
          <strong>
            {percent(
              agent.metrics
                ?.memory_percent,
            )}
          </strong>
        </div>
      </div>

      <div className="inventory-kinds">
        <span>
          Status: {
            agent.status.toUpperCase()
          }
        </span>

        <span>
          Disk: {
            percent(
              agent.metrics?.disk_percent,
            )
          }
        </span>

        <span>
          Docker: {dockerValue}
        </span>

        <span>
          Capabilities: {
            agent.capabilities.length
          }
        </span>

        <span>
          Last seen: {
            formatDate(
              agent.last_seen_at,
            )
          }
        </span>
      </div>
    </article>
  )
}

export function Infrastructure() {
  const auth = useAuth()
  const queryClient = useQueryClient()

  const token = auth.tokens?.access_token
  const workspaceId = auth.workspace?.id

  const canExecuteNetwork =
    hasPermission(
      auth.workspace?.role,
      'network.execute',
    )

  const realtimeStatus =
    useWorkspaceTelemetry()

  const agents = useQuery({
    queryKey: [
      'agents',
      workspaceId,
    ],
    queryFn: () =>
      getAgents(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  const agentList =
    agents.data ?? []

  const onlineAgentList =
    agentList.filter(
      (agent) =>
        agent.status === 'online'
        || agent.status === 'healthy',
    )

  const reportingAgents =
    onlineAgentList.filter(
      (agent) =>
        agent.metrics !== null,
    ).length

  const dockerObserved =
    onlineAgentList.some(
      (agent) =>
        typeof agent.metrics?.docker
          ?.containers_total
        === 'number',
    )

  const dockerRunning =
    onlineAgentList.reduce(
      (total, agent) =>
        total
        + (
          agent.metrics?.docker
            ?.containers_running
          ?? 0
        ),
      0,
    )

  const dockerTotal =
    onlineAgentList.reduce(
      (total, agent) =>
        total
        + (
          agent.metrics?.docker
            ?.containers_total
          ?? 0
        ),
      0,
    )

  const status = useQuery({
    queryKey: [
      'mikrotik-status',
      workspaceId,
    ],
    queryFn: () =>
      getMikroTikStatus(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
    retry: false,
  })

  const snapshot = useQuery({
    queryKey: [
      'mikrotik-snapshot',
      workspaceId,
    ],
    queryFn: () =>
      getMikroTikSnapshot(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token
      && workspaceId
      && status.isSuccess,
    ),
    refetchInterval: 30_000,
    retry: false,
  })

  const renew = useMutation({
    mutationFn: (interfaceName: string) =>
      renewMikroTikDhcp(
        token!,
        workspaceId!,
        interfaceName,
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: [
          'mikrotik-status',
          workspaceId,
        ],
      })
      await queryClient.invalidateQueries({
        queryKey: [
          'mikrotik-snapshot',
          workspaceId,
        ],
      })
    },
  })

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Infrastructure control
          </p>
          <h1>Infrastructure</h1>
          <p>
            Linux hosts, agent telemetry,
            Docker runtime and RouterOS network
            operations in one workspace view.
          </p>
        </div>
      </header>

      <section className="panel">
        <div className="panel__title">
          <Boxes size={20} />
          <h2>Linux fleet</h2>
        </div>

        <div className="inventory-kinds">
          <span>
            Agents: {
              onlineAgentList.length
            } / {agentList.length} online
          </span>

          <span>
            Telemetry: {
              reportingAgents
            } / {agentList.length}
          </span>

          <span>
            Realtime: {
              realtimeStatus.toUpperCase()
            }
          </span>

          <span>
            Docker: {
              dockerObserved
                ? `${dockerRunning} / ${dockerTotal}`
                : '—'
            }
          </span>
        </div>
      </section>

      {agents.isLoading && (
        <div className="panel">
          Loading Linux infrastructure…
        </div>
      )}

      {agents.isError && (
        <div className="auth-error">
          Linux agent inventory is unavailable.
        </div>
      )}

      {agents.isSuccess
        && agentList.length === 0
        && (
          <div className="panel empty-state">
            <Server size={28} />
            <strong>No Linux hosts</strong>
            <span>
              Hosts appear after agent
              enrollment.
            </span>
          </div>
        )}

      {agents.isSuccess
        && agentList.length > 0
        && (
          <section className="resource-grid">
            {agentList.map((agent) => (
              <LinuxHostCard
                key={agent.id}
                agent={agent}
              />
            ))}
          </section>
        )}

      <section className="panel">
        <div className="panel__title">
          <Router size={20} />
          <h2>RouterOS network</h2>
        </div>

        <p className="placeholder">
          Router health, WAN state and
          allowlisted recovery controls.
        </p>
      </section>

      {status.isLoading && (
        <div className="panel">
          Connecting to MikroTik…
        </div>
      )}

      {status.isError && (
        <div className="auth-error">
          RouterOS integration is unavailable.
          Linux infrastructure remains available.
          Configure the server-side MikroTik
          connection or verify network access.
        </div>
      )}

      {status.data && (
        <section className="resource-grid">
          <article className="resource-card">
            <header className="resource-card__header">
              <div className="agent-title">
                <Router size={20} />
                <div>
                  <strong>
                    {status.data.identity
                      ?? 'MikroTik'}
                  </strong>
                  <small>
                    RouterOS {
                      status.data.version
                      ?? 'unknown'
                    }
                  </small>
                </div>
              </div>

              {status.data.connected ? (
                <CheckCircle2 size={19} />
              ) : (
                <TriangleAlert size={19} />
              )}
            </header>

            <div className="resource-stats">
              <div>
                <Activity size={17} />
                <span>Uptime</span>
                <strong>
                  {status.data.uptime ?? '—'}
                </strong>
              </div>

              <div>
                <Network size={17} />
                <span>Default route</span>
                <strong>
                  {status.data
                    .default_route_present
                    ? 'OK'
                    : 'Missing'}
                </strong>
              </div>
            </div>

            <div className="inventory-kinds">
              <span>
                Interfaces: {
                  status.data.interface_count
                }
              </span>
              <span>
                Addresses: {
                  status.data.address_count
                }
              </span>
              <span>
                CPU: {
                  status.data.cpu_load ?? '—'
                }%
              </span>
            </div>
          </article>

          <article className="resource-card">
            <header className="resource-card__header">
              <div className="agent-title">
                <RefreshCcw size={20} />
                <div>
                  <strong>WAN</strong>
                  <small>
                    DHCP and public IP guard
                  </small>
                </div>
              </div>

              {status.data.wan_running
                && status.data.wan_dhcp_bound
                && status.data
                  .wan_ip_matches_expected
                  !== false ? (
                <CheckCircle2 size={19} />
              ) : (
                <TriangleAlert size={19} />
              )}
            </header>

            <div className="inventory-kinds">
              <span>
                Interface: {status.data.wan_interface}
              </span>
              <span>
                Link: {
                  status.data.wan_running
                    ? 'running'
                    : 'down'
                }
              </span>
              <span>
                DHCP: {
                  status.data.wan_dhcp_bound
                    ? 'bound'
                    : 'not bound'
                }
              </span>
              <span>
                WAN IP: {
                  status.data.wan_address ?? '—'
                }
              </span>
              {status.data.expected_wan_ip && (
                <span>
                  Expected IP: {
                    status.data.expected_wan_ip
                  } — {
                    status.data
                      .wan_ip_matches_expected
                      ? 'match'
                      : 'changed'
                  }
                </span>
              )}
            </div>

            {status.data.dhcp_clients.length
              === 0 && (
              <div className="empty-state">
                No DHCP client detected.
              </div>
            )}

            <div className="finding-list">
              {status.data.dhcp_clients.map(
                (client, index) => (
                  <div
                    key={
                      client.interface
                      ?? String(index)
                    }
                  >
                    <strong>
                      {client.interface
                        ?? 'unknown'}
                    </strong>
                    {' · '}
                    {client.status ?? 'unknown'}
                    {' · '}
                    {client.address ?? 'no address'}

                    {client.interface && (
                      <button
                        type="button"
                        className="sidebar-action"
                        disabled={!canExecuteNetwork || (
                          renew.isPending
                        )}
                        onClick={() =>
                          renew.mutate(
                            client.interface!,
                          )
                        }
                      >
                        Renew lease
                      </button>
                    )}
                  </div>
                ),
              )}
            </div>

            {renew.isError && (
              <div className="auth-error">
                DHCP renewal was rejected or
                failed.
              </div>
            )}

            {renew.isSuccess && (
              <div className="panel">
                DHCP renewal requested.
              </div>
            )}
          </article>
        </section>
      )}

      {snapshot.data && (
        <section className="panel">
          <h2>Router snapshot</h2>
          <div className="inventory-kinds">
            <span>
              Routes: {
                snapshot.data.routes.length
              }
            </span>
            <span>
              IP addresses: {
                snapshot.data.addresses.length
              }
            </span>
            <span>
              DNS: {
                snapshot.data.dns.servers
                ?? 'RouterOS default'
              }
            </span>
          </div>
        </section>
      )}
    </>
  )
}
