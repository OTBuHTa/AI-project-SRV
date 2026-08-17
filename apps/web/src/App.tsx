import {
  Activity,
  Bot,
  Boxes,
  BrainCircuit,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldCheck,
} from 'lucide-react'
import {
  Navigate,
  NavLink,
  Route,
  Routes,
} from 'react-router-dom'

import { useAuth } from './auth/useAuth'
import { Actions } from './pages/Actions'
import { Agents } from './pages/Agents'
import { AIAssistant } from './pages/AIAssistant'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { Resources } from './pages/Resources'
import { WorkspaceSelect } from './pages/WorkspaceSelect'

function Placeholder({
  title,
}: {
  title: string
}) {
  return (
    <div className="placeholder-page">
      <p className="eyebrow">
        AI-project SRV
      </p>
      <h1>{title}</h1>
      <p>
        This module is queued for the next
        vertical slice.
      </p>
    </div>
  )
}

const nav = [
  ['/', 'Dashboard', LayoutDashboard],
  ['/infrastructure', 'Infrastructure', Activity],
  ['/resources', 'Resources', Boxes],
  ['/agents', 'Agents', Bot],
  ['/ai', 'AI Assistant', BrainCircuit],
  ['/actions', 'Actions', ShieldCheck],
  ['/audit', 'Audit', ClipboardList],
  ['/settings', 'Settings', Settings],
] as const

function LoadingScreen() {
  return (
    <main className="auth-screen">
      <section className="auth-card">
        <p className="eyebrow">
          AI-project SRV
        </p>
        <h1>Restoring session</h1>
      </section>
    </main>
  )
}

function ProtectedShell() {
  const auth = useAuth()

  if (auth.status === 'loading') {
    return <LoadingScreen />
  }

  if (auth.status === 'anonymous') {
    return <Navigate to="/login" replace />
  }

  if (!auth.workspace) {
    return (
      <Navigate
        to="/select-workspace"
        replace
      />
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark">
            <BrainCircuit size={22} />
          </div>

          <div>
            <strong>AI-project SRV</strong>
            <span>Control Center</span>
          </div>
        </div>

        <div className="workspace-summary">
          <span>Workspace</span>
          <strong>{auth.workspace.name}</strong>
          <small>
            {auth.workspace.environment}
            {' · '}
            {auth.workspace.role}
          </small>
        </div>

        <nav>
          {nav.map(
            ([path, label, Icon]) => (
              <NavLink
                key={path}
                to={path}
                end={path === '/'}
                className={({
                  isActive,
                }) =>
                  isActive
                    ? 'nav-link active'
                    : 'nav-link'
                }
              >
                <Icon size={18} />
                {label}
              </NavLink>
            ),
          )}
        </nav>

        <div className="sidebar__footer sidebar__footer--stack">
          <div className="sidebar-user">
            <span className="status-dot" />
            <span>
              {auth.user?.display_name
                ?? auth.user?.email}
            </span>
          </div>

          <button
            type="button"
            className="sidebar-action"
            onClick={auth.logout}
          >
            <LogOut size={15} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Routes>
          <Route
            path="/"
            element={<Dashboard />}
          />
          <Route
            path="/infrastructure"
            element={
              <Placeholder title="Infrastructure" />
            }
          />
          <Route
            path="/resources"
            element={<Resources />}
          />
          <Route
            path="/agents"
            element={<Agents />}
          />
          <Route
            path="/ai"
            element={<AIAssistant />}
          />
          <Route
            path="/actions"
            element={<Actions />}
          />
          <Route
            path="/audit"
            element={
              <Placeholder title="Audit" />
            }
          />
          <Route
            path="/settings"
            element={
              <Placeholder title="Settings" />
            }
          />
          <Route
            path="*"
            element={
              <Navigate to="/" replace />
            }
          />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const auth = useAuth()

  if (auth.status === 'loading') {
    return <LoadingScreen />
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/select-workspace"
        element={<WorkspaceSelect />}
      />

      <Route
        path="/*"
        element={<ProtectedShell />}
      />
    </Routes>
  )
}
