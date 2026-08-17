import {
  useState,
  type FormEvent,
} from 'react'
import {
  BrainCircuit,
  LogIn,
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

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
      const workspace = await auth.login(
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
            Secure access
          </p>
          <h1>Sign in</h1>
          <p>
            Authenticate to access your
            infrastructure workspace.
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

          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
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
            <LogIn size={17} />
            {submitting
              ? 'Signing in...'
              : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  )
}
