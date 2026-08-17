import {
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  getCurrentUser,
  getWorkspaces,
  login as loginRequest,
  refreshSession,
  type CurrentUser,
  type TokenResponse,
  type Workspace,
} from '../api/auth'
import { ApiError } from '../api/http'
import {
  clearSession,
  clearStoredWorkspace,
  getStoredWorkspace,
  getTokens,
  setStoredWorkspace,
  setTokens,
} from './session'
import {
  AuthContext,
  type AuthStatus,
} from './AuthContext'

export function AuthProvider({
  children,
}: {
  children: ReactNode
}) {
  const [status, setStatus] =
    useState<AuthStatus>('loading')

  const [tokensState, setTokensState] =
    useState<TokenResponse | null>(null)

  const [user, setUser] =
    useState<CurrentUser | null>(null)

  const [workspaces, setWorkspaces] =
    useState<Workspace[]>([])

  const [workspace, setWorkspace] =
    useState<Workspace | null>(null)

  useEffect(() => {
    let cancelled = false

    async function restore() {
      let tokens = getTokens()
      const storedWorkspace = getStoredWorkspace()

      if (!tokens) {
        if (!cancelled) {
          setStatus('anonymous')
        }
        return
      }

      try {
        let currentUser: CurrentUser

        try {
          currentUser = await getCurrentUser(
            tokens.access_token,
          )
        } catch (error) {
          if (
            !(error instanceof ApiError)
            || error.status !== 401
          ) {
            throw error
          }

          tokens = await refreshSession(
            tokens.refresh_token,
            storedWorkspace?.id,
          )

          setTokens(tokens)

          currentUser = await getCurrentUser(
            tokens.access_token,
          )
        }

        const availableWorkspaces =
          await getWorkspaces(tokens.access_token)

        const restoredWorkspace =
          storedWorkspace
            ? (
                availableWorkspaces.find(
                  (item) =>
                    item.id === storedWorkspace.id,
                ) ?? null
              )
            : null

        if (
          storedWorkspace
          && !restoredWorkspace
        ) {
          clearStoredWorkspace()
        }

        if (!cancelled) {
          setTokensState(tokens)
          setUser(currentUser)
          setWorkspaces(availableWorkspaces)
          setWorkspace(restoredWorkspace)
          setStatus('authenticated')
        }
      } catch {
        clearSession()

        if (!cancelled) {
          setTokensState(null)
          setUser(null)
          setWorkspaces([])
          setWorkspace(null)
          setStatus('anonymous')
        }
      }
    }

    void restore()

    return () => {
      cancelled = true
    }
  }, [])

  async function login(
    email: string,
    password: string,
  ): Promise<Workspace | null> {
    const initialTokens = await loginRequest(
      email,
      password,
    )

    setTokens(initialTokens)

    const [currentUser, availableWorkspaces] =
      await Promise.all([
        getCurrentUser(initialTokens.access_token),
        getWorkspaces(initialTokens.access_token),
      ])

    let activeTokens = initialTokens
    let activeWorkspace: Workspace | null = null

    if (availableWorkspaces.length === 1) {
      activeWorkspace = availableWorkspaces[0]

      activeTokens = await refreshSession(
        initialTokens.refresh_token,
        activeWorkspace.id,
      )

      setTokens(activeTokens)
      setStoredWorkspace(activeWorkspace)
    } else {
      clearStoredWorkspace()
    }

    setTokensState(activeTokens)
    setUser(currentUser)
    setWorkspaces(availableWorkspaces)
    setWorkspace(activeWorkspace)
    setStatus('authenticated')

    return activeWorkspace
  }

  async function selectWorkspace(
    workspaceId: string,
  ) {
    if (!tokensState) {
      throw new Error('session_not_available')
    }

    const selected = workspaces.find(
      (item) => item.id === workspaceId,
    )

    if (!selected) {
      throw new Error('workspace_not_available')
    }

    const nextTokens = await refreshSession(
      tokensState.refresh_token,
      selected.id,
    )

    setTokens(nextTokens)
    setStoredWorkspace(selected)

    setTokensState(nextTokens)
    setWorkspace(selected)
  }

  function logout() {
    clearSession()
    setTokensState(null)
    setUser(null)
    setWorkspaces([])
    setWorkspace(null)
    setStatus('anonymous')
  }

  return (
    <AuthContext.Provider
      value={{
        status,
        tokens: tokensState,
        user,
        workspaces,
        workspace,
        login,
        selectWorkspace,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
