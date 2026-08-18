export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function extractDetail(body: unknown): string {
  if (
    typeof body === 'object'
    && body !== null
    && 'detail' in body
  ) {
    const detail = body.detail

    if (typeof detail === 'string') {
      return detail
    }
  }

  return 'request_failed'
}

export async function apiJson<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(url, init)

  const body = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    throw new ApiError(
      response.status,
      extractDetail(body),
    )
  }

  return body as T
}

export function bearerHeaders(
  accessToken: string,
): HeadersInit {
  return {
    Authorization: `Bearer ${accessToken}`,
  }
}


export function workspaceHeaders(
  accessToken: string,
  workspaceId: string,
): HeadersInit {
  return {
    ...bearerHeaders(accessToken),
    'X-Workspace-ID': workspaceId,
  }
}
