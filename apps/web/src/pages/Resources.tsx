import {
  Boxes,
  CheckCircle2,
  Container,
  Server,
  TriangleAlert,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

import {
  getAgents,
  getInventorySummary,
  getResourceHealth,
  type Agent,
} from '../api/agents'
import { useAuth } from '../auth/useAuth'

function ResourceCard({
  agent,
  accessToken,
}: {
  agent: Agent
  accessToken: string
}) {
  const health = useQuery({
    queryKey: [
      'resource-health',
      agent.resource_id,
    ],
    queryFn: () =>
      getResourceHealth(
        accessToken,
        agent.resource_id,
      ),
    refetchInterval: 10_000,
  })

  const inventory = useQuery({
    queryKey: [
      'inventory-summary',
      agent.resource_id,
    ],
    queryFn: () =>
      getInventorySummary(
        accessToken,
        agent.resource_id,
      ),
    refetchInterval: 30_000,
  })

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
        </div>
      )}
    </article>
  )
}

export function Resources() {
  const auth = useAuth()

  const token =
    auth.tokens?.access_token

  const agents = useQuery({
    queryKey: [
      'agents',
      auth.workspace?.id,
    ],
    queryFn: () =>
      getAgents(token!),
    enabled: Boolean(
      token && auth.workspace,
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
          && agents.data?.map((agent) => (
            <ResourceCard
              key={agent.resource_id}
              agent={agent}
              accessToken={token}
            />
          ))}
      </section>
    </>
  )
}
