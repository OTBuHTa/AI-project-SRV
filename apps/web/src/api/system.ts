export type ApiInfo = {
  name: string
  version: string
  build_revision: string
  phase: string
}

export type HealthStatus = {
  status: string
  service: string
  environment: string
  version: string
  build_revision: string
}

export type ReadyStatus = {
  status: string
  checks: {
    database: boolean
    redis: boolean
  }
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(
      typeof body?.detail === 'string'
        ? body.detail
        : `HTTP ${response.status}`,
    )
  }

  return body as T
}

export function getApiInfo() {
  return getJson<ApiInfo>('/api/v1')
}

export function getHealth() {
  return getJson<HealthStatus>('/health')
}

export async function getReady(): Promise<ReadyStatus> {
  const response = await fetch('/ready')
  const body = await response.json().catch(() => null)

  if (response.ok) {
    return body as ReadyStatus
  }

  if (response.status === 503 && body?.detail?.checks) {
    return {
      status: 'not_ready',
      checks: body.detail.checks,
    }
  }

  throw new Error(`HTTP ${response.status}`)
}
