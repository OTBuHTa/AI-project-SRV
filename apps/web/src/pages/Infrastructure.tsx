import {
  Activity,
  CheckCircle2,
  Network,
  RefreshCcw,
  Router,
  TriangleAlert,
} from 'lucide-react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  getMikroTikSnapshot,
  getMikroTikStatus,
  renewMikroTikDhcp,
} from '../api/mikrotik'
import { useAuth } from '../auth/useAuth'

export function Infrastructure() {
  const auth = useAuth()
  const queryClient = useQueryClient()

  const token = auth.tokens?.access_token
  const workspaceId = auth.workspace?.id

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
            Network automation
          </p>
          <h1>Infrastructure</h1>
          <p>
            MikroTik RouterOS health,
            routing and safe recovery controls.
          </p>
        </div>
      </header>

      {status.isLoading && (
        <div className="panel">
          Connecting to MikroTik…
        </div>
      )}

      {status.isError && (
        <div className="auth-error">
          MikroTik integration is unavailable.
          Configure the server-side RouterOS
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
                  <strong>WAN DHCP</strong>
                  <small>
                    Allowlisted recovery action
                  </small>
                </div>
              </div>
            </header>

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
                        disabled={
                          renew.isPending
                        }
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
