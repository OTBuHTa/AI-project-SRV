import {
  Activity,
  Archive,
  Bell,
  Bot,
  Boxes,
  BrainCircuit,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
} from 'lucide-react'
import {
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'

import {
  loginPath,
  workspaceSelectPath,
} from './auth/redirect'
import { hasPermission } from './auth/permissions'
import { useAuth } from './auth/useAuth'
import { Actions } from './pages/Actions'
import { Agents } from './pages/Agents'
import { AIAssistant } from './pages/AIAssistant'
import { Audit } from './pages/Audit'
import { Backups } from './pages/Backups'
import { Dashboard } from './pages/Dashboard'
import { Infrastructure } from './pages/Infrastructure'
import { Notifications } from './pages/Notifications'
import { Login } from './pages/Login'
import { Resources } from './pages/Resources'
import { WorkspaceSelect } from './pages/WorkspaceSelect'

const nav = [
  ['/', 'Dashboard', LayoutDashboard, []],
  [
    '/infrastructure',
    'Infrastructure',
    Activity,
    ['agent.read', 'network.read'],
  ],
  ['/resources', 'Resources', Boxes, ['resource.read']],
  ['/agents', 'Agents', Bot, ['agent.read']],
  ['/ai', 'AI Assistant', BrainCircuit, ['resource.read']],
  ['/actions', 'Actions', ShieldCheck, ['action.read']],
  [
    '/notifications',
    'Notifications',
    Bell,
    ['workspace.read'],
  ],
  ['/backups', 'Backups', Archive, ['workspace.read']],
  ['/audit', 'Audit', ClipboardList, ['audit.read']],
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
  const location = useLocation()

  const next = (
    location.pathname
    + location.search
    + location.hash
  )

  if (auth.status === 'loading') {
    return <LoadingScreen />
  }

  if (auth.status === 'anonymous') {
    return (
      <Navigate
        to={loginPath(next)}
        replace
      />
    )
  }

  if (!auth.workspace) {
    return (
      <Navigate
        to={workspaceSelectPath(next)}
        replace
      />
    )
  }

  const canAccess = (
    permissions: readonly string[],
  ) =>
    permissions.every((permission) =>
      hasPermission(
        auth.workspace?.role,
        permission,
      ),
    )

  const visibleNav =
    nav.filter(
      ([, , , permissions]) =>
        canAccess(permissions),
    )

  const currentNav =
    visibleNav.find(([path]) =>
      path === '/'
        ? location.pathname === '/'
        : location.pathname.startsWith(path),
    )

  const currentSection =
    currentNav?.[1] ?? 'Control Center'

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
          {visibleNav.map(
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
        <header className="shell-header">
          <div className="shell-header__context">
            <span className="shell-header__eyebrow">
              {auth.workspace.name}
            </span>
            <strong>{currentSection}</strong>
          </div>

          <div className="shell-header__meta">
            <span className="shell-header__environment">
              {auth.workspace.environment}
            </span>
            <span className="shell-header__role">
              {auth.workspace.role}
            </span>
            <span
              className="shell-header__status"
              title="Authenticated workspace session"
            >
              <span className="status-dot" />
              Connected
            </span>
          </div>
        </header>

        <div className="shell-content">
          <Routes>
          <Route
            path="/"
            element={<Dashboard />}
          />
          <Route
            path="/infrastructure"
            element={
              canAccess([
                'agent.read',
                'network.read',
              ])
                ? <Infrastructure />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="/resources"
            element={
              canAccess(['resource.read'])
                ? <Resources />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="/agents"
            element={
              canAccess(['agent.read'])
                ? <Agents />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="/ai"
            element={
              canAccess(['resource.read'])
                ? <AIAssistant />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="/actions"
            element={
              canAccess(['action.read'])
                ? <Actions />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="/notifications"
            element={
              canAccess(['workspace.read'])
                ? <Notifications />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="/backups"
            element={
              canAccess(['workspace.read'])
                ? <Backups />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="/audit"
            element={
              canAccess(['audit.read'])
                ? <Audit />
                : <Navigate to="/" replace />
            }
          />
          <Route
            path="*"
            element={
              <Navigate to="/" replace />
            }
          />
          </Routes>
        </div>
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
