import {
  useState,
  type FormEvent,
} from 'react'
import {
  BrainCircuit,
  LogIn,
  UserPlus,
} from 'lucide-react'
import {
  Navigate,
  useNavigate,
  useSearchParams,
} from 'react-router-dom'

import { ApiError } from '../api/http'
import {
  safeNext,
  workspaceSelectPath,
} from '../auth/redirect'
import { useAuth } from '../auth/useAuth'

export function Login() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const next = safeNext(
    searchParams.get('next'),
  )

  const [mode, setMode] =
    useState<'login' | 'bootstrap'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [
    displayName,
    setDisplayName,
  ] = useState('')
  const [
    organizationName,
    setOrganizationName,
  ] = useState('')
  const [
    organizationSlug,
    setOrganizationSlug,
  ] = useState('')
  const [
    workspaceName,
    setWorkspaceName,
  ] = useState('Main')
  const [error, setError] =
    useState<string | null>(null)
  const [submitting, setSubmitting] =
    useState(false)

  if (
    auth.status === 'authenticated'
    && auth.workspace
  ) {
    return (
      <Navigate
        to={next}
        replace
      />
    )
  }

  async function submit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const workspace =
        mode === 'bootstrap'
          ? await auth.bootstrap({
              email,
              password,
              display_name:
                displayName.trim() || null,
              organization_name:
                organizationName.trim(),
              organization_slug:
                organizationSlug.trim(),
              workspace_name:
                workspaceName.trim(),
            })
          : await auth.login(
              email,
              password,
            )

      navigate(
        workspace
          ? next
          : workspaceSelectPath(next),
        { replace: true },
      )
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.detail)
      } else {
        setError('authentication_failed')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="brand__mark">
            <BrainCircuit size={24} />
          </div>

          <div>
            <strong>AI-project SRV</strong>
            <span>Web Control Center</span>
          </div>
        </div>

        <div className="auth-heading">
          <p className="eyebrow">
            {mode === 'bootstrap'
              ? 'First-time setup'
              : 'Secure access'}
          </p>
          <h1>
            {mode === 'bootstrap'
              ? 'Initialize platform'
              : 'Sign in'}
          </h1>
          <p>
            {mode === 'bootstrap'
              ? (
                  'Create the initial owner, '
                  + 'organization and workspace.'
                )
              : (
                  'Authenticate to access your '
                  + 'infrastructure workspace.'
                )}
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={submit}
        >
          <label>
            Email
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
            />
          </label>

          {mode === 'bootstrap' && (
            <>
              <label>
                Display name
                <input
                  type="text"
                  autoComplete="name"
                  maxLength={160}
                  value={displayName}
                  onChange={(event) =>
                    setDisplayName(
                      event.target.value,
                    )
                  }
                />
              </label>

              <label>
                Organization name
                <input
                  type="text"
                  minLength={2}
                  maxLength={160}
                  value={organizationName}
                  onChange={(event) =>
                    setOrganizationName(
                      event.target.value,
                    )
                  }
                  required
                />
              </label>

              <label>
                Organization slug
                <input
                  type="text"
                  minLength={3}
                  maxLength={160}
                  pattern="[a-z0-9][a-z0-9-]{1,158}[a-z0-9]"
                  value={organizationSlug}
                  onChange={(event) =>
                    setOrganizationSlug(
                      event.target.value,
                    )
                  }
                  required
                />
              </label>

              <label>
                Workspace name
                <input
                  type="text"
                  minLength={1}
                  maxLength={160}
                  value={workspaceName}
                  onChange={(event) =>
                    setWorkspaceName(
                      event.target.value,
                    )
                  }
                  required
                />
              </label>
            </>
          )}

          <label>
            Password
            <input
              type="password"
              autoComplete={
                mode === 'bootstrap'
                  ? 'new-password'
                  : 'current-password'
              }
              minLength={
                mode === 'bootstrap'
                  ? 12
                  : undefined
              }
              maxLength={
                mode === 'bootstrap'
                  ? 128
                  : undefined
              }
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              required
            />
          </label>

          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <button
            className="primary-button"
            type="submit"
            disabled={submitting}
          >
            {mode === 'bootstrap' ? (
              <UserPlus size={17} />
            ) : (
              <LogIn size={17} />
            )}
            {submitting
              ? (
                  mode === 'bootstrap'
                    ? 'Initializing...'
                    : 'Signing in...'
                )
              : (
                  mode === 'bootstrap'
                    ? 'Initialize platform'
                    : 'Sign in'
                )}
          </button>

          <button
            className="sidebar-action"
            type="button"
            disabled={submitting}
            onClick={() => {
              setError(null)
              setPassword('')
              setMode(
                mode === 'login'
                  ? 'bootstrap'
                  : 'login',
              )
            }}
          >
            {mode === 'login' ? (
              <UserPlus size={17} />
            ) : (
              <LogIn size={17} />
            )}
            {mode === 'login'
              ? 'First-time setup'
              : 'Back to sign in'}
          </button>
        </form>
      </section>
    </main>
  )
}
