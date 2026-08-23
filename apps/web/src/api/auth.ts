import {
  apiJson,
  bearerHeaders,
  workspaceHeaders,
} from './http'

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export type CurrentUser = {
  id: string
  email: string
  display_name: string | null
  status: string
}

export type Workspace = {
  id: string
  organization_id: string
  name: string
  environment: string
  status: string
  role: string
}

export type BootstrapRequest = {
  email: string
  password: string
  display_name: string | null
  organization_name: string
  organization_slug: string
  workspace_name: string
}

export function bootstrap(
  payload: BootstrapRequest,
) {
  return apiJson<TokenResponse>(
    '/api/v1/auth/bootstrap',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export function login(
  email: string,
  password: string,
) {
  return apiJson<TokenResponse>(
    '/api/v1/auth/login',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
      }),
    },
  )
}

export function refreshSession(
  refreshToken: string,
  workspaceId?: string,
) {
  return apiJson<TokenResponse>(
    '/api/v1/auth/refresh',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
        workspace_id: workspaceId ?? null,
      }),
    },
  )
}

export function getCurrentUser(
  accessToken: string,
) {
  return apiJson<CurrentUser>(
    '/api/v1/auth/me',
    {
      headers: bearerHeaders(accessToken),
    },
  )
}

export function getWorkspaces(
  accessToken: string,
) {
  return apiJson<Workspace[]>(
    '/api/v1/workspaces',
    {
      headers: bearerHeaders(accessToken),
    },
  )
}

export function getCurrentWorkspace(
  accessToken: string,
  workspaceId: string,
) {
  return apiJson<Workspace>(
    '/api/v1/workspaces/current',
    {
      headers: workspaceHeaders(
        accessToken,
        workspaceId,
      ),
    },
  )
}
