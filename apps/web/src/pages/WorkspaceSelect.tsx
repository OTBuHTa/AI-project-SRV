import {
  useState,
} from 'react'
import {
  Building2,
  ChevronRight,
} from 'lucide-react'
import {
  Navigate,
  useNavigate,
  useSearchParams,
} from 'react-router-dom'

import {
  loginPath,
  safeNext,
} from '../auth/redirect'
import { useAuth } from '../auth/useAuth'

export function WorkspaceSelect() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const next = safeNext(
    searchParams.get('next'),
  )

  const [error, setError] =
    useState<string | null>(null)

  const [selecting, setSelecting] =
    useState<string | null>(null)

  if (auth.status === 'anonymous') {
    return (
      <Navigate
        to={loginPath(next)}
        replace
      />
    )
  }

  async function select(id: string) {
    setError(null)
    setSelecting(id)

    try {
      await auth.selectWorkspace(id)
      navigate(next, { replace: true })
    } catch {
      setError('workspace_selection_failed')
    } finally {
      setSelecting(null)
    }
  }

  return (
    <main className="auth-screen">
      <section className="workspace-card">
        <div className="auth-heading">
          <p className="eyebrow">
            AI-project SRV
          </p>
          <h1>Select workspace</h1>
          <p>
            Choose the infrastructure context
            for this session.
          </p>
        </div>

        <div className="workspace-list">
          {auth.workspaces.map((workspace) => (
            <button
              key={workspace.id}
              className="workspace-option"
              type="button"
              disabled={selecting !== null}
              onClick={() =>
                void select(workspace.id)
              }
            >
              <Building2 size={20} />

              <span>
                <strong>{workspace.name}</strong>
                <small>
                  {workspace.environment}
                  {' · '}
                  {workspace.role}
                </small>
              </span>

              <ChevronRight size={18} />
            </button>
          ))}
        </div>

        {auth.workspaces.length === 0 && (
          <div className="auth-error">
            No workspace memberships found.
          </div>
        )}

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}
      </section>
    </main>
  )
}
