import { createContext } from 'react'

import type {
  CurrentUser,
  TokenResponse,
  Workspace,
} from '../api/auth'

export type AuthStatus =
  | 'loading'
  | 'anonymous'
  | 'authenticated'

export type AuthContextValue = {
  status: AuthStatus
  tokens: TokenResponse | null
  user: CurrentUser | null
  workspaces: Workspace[]
  workspace: Workspace | null
  login: (
    email: string,
    password: string,
  ) => Promise<Workspace | null>
  selectWorkspace: (
    workspaceId: string,
  ) => Promise<void>
  logout: () => void
}

export const AuthContext =
  createContext<AuthContextValue | null>(null)
