import {
  Activity,
  Bot,
  Boxes,
  BrainCircuit,
  ClipboardList,
  LayoutDashboard,
  Settings,
} from 'lucide-react'
import {
  Navigate,
  NavLink,
  Route,
  Routes,
} from 'react-router-dom'

import { Dashboard } from './pages/Dashboard'

function Placeholder({ title }: { title: string }) {
  return (
    <div className="placeholder-page">
      <p className="eyebrow">AI-project SRV</p>
      <h1>{title}</h1>
      <p>This module is queued for the next vertical slice.</p>
    </div>
  )
}

const nav = [
  ['/', 'Dashboard', LayoutDashboard],
  ['/infrastructure', 'Infrastructure', Activity],
  ['/resources', 'Resources', Boxes],
  ['/agents', 'Agents', Bot],
  ['/ai', 'AI Assistant', BrainCircuit],
  ['/audit', 'Audit', ClipboardList],
  ['/settings', 'Settings', Settings],
] as const

export default function App() {
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

        <nav>
          {nav.map(([path, label, Icon]) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          <span className="status-dot" />
          Backend connected
        </div>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route
            path="/infrastructure"
            element={<Placeholder title="Infrastructure" />}
          />
          <Route
            path="/resources"
            element={<Placeholder title="Resources" />}
          />
          <Route
            path="/agents"
            element={<Placeholder title="Agents" />}
          />
          <Route
            path="/ai"
            element={<Placeholder title="AI Assistant" />}
          />
          <Route
            path="/audit"
            element={<Placeholder title="Audit" />}
          />
          <Route
            path="/settings"
            element={<Placeholder title="Settings" />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
