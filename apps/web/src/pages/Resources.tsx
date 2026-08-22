import {
  useState,
} from 'react'
import {
  Activity,
  Boxes,
  CheckCircle2,
  Container,
  Cpu,
  HardDrive,
  MemoryStick,
  Server,
  TriangleAlert,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import {
  getAgents,
  getAgentTelemetry,
  getInventorySummary,
  getResourceHealth,
  getResourceInventory,
  type Agent,
  type InventoryLifecycleStatus,
} from '../api/agents'
import { useAuth } from '../auth/useAuth'

function ResourceCard({
  agent,
  accessToken,
  workspaceId,
}: {
  agent: Agent
  accessToken: string
  workspaceId: string
}) {
  const [
    inventoryExpanded,
    setInventoryExpanded,
  ] = useState(false)

  const [
    inventoryKind,
    setInventoryKind,
  ] = useState<string | undefined>()

  const [
    inventoryLifecycle,
    setInventoryLifecycle,
  ] = useState<
    InventoryLifecycleStatus | undefined
  >()

  const health = useQuery({
    queryKey: [
      'resource-health',
      workspaceId,
      agent.resource_id,
    ],
    queryFn: () =>
      getResourceHealth(
        accessToken,
        workspaceId,
        agent.resource_id,
      ),
    refetchInterval: 10_000,
  })

  const inventory = useQuery({
    queryKey: [
      'inventory-summary',
      workspaceId,
      agent.resource_id,
    ],
    queryFn: () =>
      getInventorySummary(
        accessToken,
        workspaceId,
        agent.resource_id,
      ),
    refetchInterval: 30_000,
  })

  const inventoryItems = useQuery({
    queryKey: [
      'inventory-items',
      workspaceId,
      agent.resource_id,
      inventoryKind ?? 'all',
      inventoryLifecycle ?? 'all',
    ],
    queryFn: () =>
      getResourceInventory(
        accessToken,
        workspaceId,
        agent.resource_id,
        {
          kind: inventoryKind,
          lifecycleStatus:
            inventoryLifecycle,
        },
      ),
    enabled: inventoryExpanded,
    refetchInterval:
      inventoryExpanded
        ? 30_000
        : false,
  })

  const telemetry = useQuery({
    queryKey: [
      'agent-telemetry',
      workspaceId,
      agent.id,
    ],
    queryFn: () =>
      getAgentTelemetry(
        accessToken,
        workspaceId,
        agent.id,
        12,
      ),
    refetchInterval: 30_000,
  })

  const latestTelemetry =
    telemetry.data?.at(-1)

  const healthy =
    health.data?.severity === 'ok'
    || health.data?.severity === 'healthy'
    || health.data?.health_score === 100

  return (
    <article className="resource-card">
      <header className="resource-card__header">
        <div className="agent-title">
          <Server size={20} />

          <div>
            <strong>{agent.hostname}</strong>
            <small>
              {agent.resource_id}
            </small>
          </div>
        </div>

        {health.isSuccess && (
          healthy ? (
            <CheckCircle2 size={19} />
          ) : (
            <TriangleAlert size={19} />
          )
        )}
      </header>

      <div className="resource-score">
        <span>Health score</span>
        <strong>
          {health.data?.health_score ?? '—'}
        </strong>
        <small>
          {health.data?.severity ?? 'loading'}
        </small>
      </div>

      <div className="resource-stats">
        <div>
          <Boxes size={17} />
          <span>Inventory</span>
          <strong>
            {inventory.data?.total_items ?? '—'}
          </strong>
        </div>

        <div>
          <Container size={17} />
          <span>Docker</span>
          <strong>
            {agent.metrics?.docker
              ?.containers_running ?? '—'}
          </strong>
        </div>
      </div>

      <div className="resource-stats">
        <div>
          <Cpu size={17} />
          <span>CPU</span>
          <strong>
            {typeof latestTelemetry
              ?.cpu_percent === 'number'
              ? `${Math.round(
                  latestTelemetry.cpu_percent,
                )}%`
              : '—'}
          </strong>
        </div>

        <div>
          <MemoryStick size={17} />
          <span>Memory</span>
          <strong>
            {typeof latestTelemetry
              ?.memory_percent === 'number'
              ? `${Math.round(
                  latestTelemetry.memory_percent,
                )}%`
              : '—'}
          </strong>
        </div>

        <div>
          <HardDrive size={17} />
          <span>Disk</span>
          <strong>
            {typeof latestTelemetry
              ?.disk_percent === 'number'
              ? `${Math.round(
                  latestTelemetry.disk_percent,
                )}%`
              : '—'}
          </strong>
        </div>

        <div>
          <Activity size={17} />
          <span>Load 1m</span>
          <strong>
            {latestTelemetry?.load_1m
              ?? '—'}
          </strong>
        </div>
      </div>

      {health.data?.findings
        && health.data.findings.length > 0
        && (
          <div className="finding-list">
            {health.data.findings.map(
              (finding) => (
                <div key={finding}>
                  {finding}
                </div>
              ),
            )}
          </div>
        )}

      {inventory.data && (
        <div className="inventory-kinds">
          {Object.entries(
            inventory.data.kinds,
          ).map(([kind, count]) => (
            <span key={kind}>
              {kind}: {count}
            </span>
          ))}

          {Object.entries(
            inventory.data.lifecycle,
          ).map(([state, count]) => (
            <span key={`lifecycle-${state}`}>
              {state}: {count}
            </span>
          ))}
        </div>
      )}

      <button
        type="button"
        className="sidebar-action"
        aria-expanded={inventoryExpanded}
        onClick={() =>
          setInventoryExpanded(
            (value) => !value,
          )
        }
      >
        {inventoryExpanded
          ? 'Hide inventory detail'
          : 'Show inventory detail'}
      </button>

      {inventoryExpanded && (
        <section>
          <div className="inventory-kinds">
            <span>Kind:</span>

            <button
              type="button"
              className="sidebar-action"
              disabled={
                inventoryKind === undefined
              }
              onClick={() =>
                setInventoryKind(undefined)
              }
            >
              all
            </button>

            {Object.keys(
              inventory.data?.kinds ?? {},
            ).map((kind) => (
              <button
                type="button"
                className="sidebar-action"
                key={kind}
                disabled={
                  inventoryKind === kind
                }
                onClick={() =>
                  setInventoryKind(kind)
                }
              >
                {kind}
              </button>
            ))}
          </div>

          <div className="inventory-kinds">
            <span>Lifecycle:</span>

            <button
              type="button"
              className="sidebar-action"
              disabled={
                inventoryLifecycle
                  === undefined
              }
              onClick={() =>
                setInventoryLifecycle(
                  undefined,
                )
              }
            >
              all
            </button>

            {(
              [
                'observed',
                'stale',
                'absent',
              ] as const
            ).map((state) => (
              <button
                type="button"
                className="sidebar-action"
                key={state}
                disabled={
                  inventoryLifecycle
                    === state
                }
                onClick={() =>
                  setInventoryLifecycle(
                    state,
                  )
                }
              >
                {state}
              </button>
            ))}
          </div>

          {inventoryItems.isLoading && (
            <div className="placeholder">
              Loading inventory detail…
            </div>
          )}

          {inventoryItems.isError && (
            <div className="auth-error">
              Inventory detail unavailable.
            </div>
          )}

          {inventoryItems.isSuccess
            && inventoryItems.data.length
              === 0
            && (
              <div className="empty-state">
                No inventory items match
                the selected filters.
              </div>
            )}

          {inventoryItems.isSuccess
            && inventoryItems.data.length
              > 0
            && (
              <>
                <div className="inventory-kinds">
                  <span>
                    Items: {
                      inventoryItems
                        .data.length
                    }
                  </span>

                  {inventoryKind && (
                    <span>
                      Kind: {inventoryKind}
                    </span>
                  )}

                  {inventoryLifecycle && (
                    <span>
                      Lifecycle: {
                        inventoryLifecycle
                      }
                    </span>
                  )}
                </div>

                <div className="finding-list">
                  {inventoryItems.data.map(
                    (item) => (
                      <div key={item.id}>
                        <strong>
                          {item.name}
                        </strong>

                        {' · '}
                        {item.kind}
                        {' · '}

                        <span className="status-badge">
                          {
                            item.lifecycle_status
                          }
                        </span>

                        <div className="inventory-kinds">
                          <span>
                            Status: {
                              item.status
                            }
                          </span>

                          <span>
                            External ID: {
                              item.external_id
                            }
                          </span>

                          <span>
                            Observed: {
                              new Date(
                                item.observed_at,
                              ).toLocaleString()
                            }
                          </span>

                          <span>
                            Last seen: {
                              item.last_seen_at
                                ? new Date(
                                    item.last_seen_at,
                                  )
                                    .toLocaleString()
                                : '—'
                            }
                          </span>

                          <span>
                            Attributes: {
                              Object.keys(
                                item.attributes,
                              ).length
                            }
                          </span>
                        </div>
                      </div>
                    ),
                  )}
                </div>
              </>
            )}
        </section>
      )}

      {telemetry.isSuccess && (
        <div className="inventory-kinds">
          <span>
            Telemetry points: {
              telemetry.data.length
            }
          </span>

          <span>
            Last sample: {
              latestTelemetry
                ? new Date(
                    latestTelemetry.timestamp,
                  ).toLocaleString()
                : '—'
            }
          </span>
        </div>
      )}
    </article>
  )
}

export function Resources() {
  const auth = useAuth()

  const token =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

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

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Workspace inventory
          </p>
          <h1>Resources</h1>
          <p>
            Agent-backed hosts, health and
            discovered inventory.
          </p>
        </div>
      </header>

      {agents.isLoading && (
        <div className="panel">
          Loading resources…
        </div>
      )}

      {agents.isError && (
        <div className="auth-error">
          Failed to load resources.
        </div>
      )}

      {agents.data?.length === 0 && (
        <div className="panel empty-state">
          <Server size={28} />
          <strong>No resources</strong>
          <span>
            Resources appear after agent
            enrollment.
          </span>
        </div>
      )}

      <section className="resource-grid">
        {token
          && workspaceId
          && agents.data?.map((agent) => (
            <ResourceCard
              key={agent.resource_id}
              agent={agent}
              accessToken={token}
              workspaceId={workspaceId}
            />
          ))}
      </section>
    </>
  )
}
