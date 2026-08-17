import type {
  TokenResponse,
  Workspace,
} from '../api/auth'

const TOKENS_KEY = 'ai-srv.tokens'
const WORKSPACE_KEY = 'ai-srv.workspace'

export function getTokens(): TokenResponse | null {
  const raw = sessionStorage.getItem(TOKENS_KEY)

  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as TokenResponse
  } catch {
    sessionStorage.removeItem(TOKENS_KEY)
    return null
  }
}

export function setTokens(tokens: TokenResponse) {
  sessionStorage.setItem(
    TOKENS_KEY,
    JSON.stringify(tokens),
  )
}

export function getStoredWorkspace(): Workspace | null {
  const raw = sessionStorage.getItem(WORKSPACE_KEY)

  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as Workspace
  } catch {
    sessionStorage.removeItem(WORKSPACE_KEY)
    return null
  }
}

export function setStoredWorkspace(workspace: Workspace) {
  sessionStorage.setItem(
    WORKSPACE_KEY,
    JSON.stringify(workspace),
  )
}

export function clearStoredWorkspace() {
  sessionStorage.removeItem(WORKSPACE_KEY)
}

export function clearSession() {
  sessionStorage.removeItem(TOKENS_KEY)
  sessionStorage.removeItem(WORKSPACE_KEY)
}
