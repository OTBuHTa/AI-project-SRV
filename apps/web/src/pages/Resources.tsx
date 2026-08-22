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
  type Agent,
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
