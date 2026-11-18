import { useEffect, useRef, useState } from 'react'
import { BrowserRouter, Link, NavLink, Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { App as LocalDemo } from './App'
import { AuthProvider } from '../features/auth/AuthProvider'
import { accountApi } from '../features/auth/authClient'
import { useAuth } from '../features/auth/authContext'
import { AccountView, AuthForm, FormNotice, SessionGate } from '../features/auth/AuthViews'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { Projects, ProjectDetail } from '../features/projects/Projects'
import { RunDetail } from '../features/projects/Runs'
import { Explorer } from '../features/explorer/Explorer'
import { WhatIf, SavedScenario } from '../features/explorer/Scenarios'
import { Dashboard } from '../features/projects/Dashboard'
import { SavedReports } from '../features/reports/SavedReports'
import { WorkspaceIcon } from '../components/WorkspaceIcon'
import { ThemeToggle } from '../components/ThemeToggle'
import { ThemeController } from './theme'

function NavigationFocus() {
  const { pathname } = useLocation()
  useEffect(() => {
    document.title = 'SmartRegression AI · Không gian cá nhân'
    const heading = document.querySelector<HTMLElement>('h1')
    heading?.setAttribute('tabindex', '-1')
    heading?.focus({ preventScroll: true })
  }, [pathname])
  return null
}

function Shell() {
  const { state, clear } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [confirmLogout, setConfirmLogout] = useState(false)
  const [navigationOpen, setNavigationOpen] = useState(false)
  const inFlight = useRef(false)
  useEffect(() => {
    if (!navigationOpen) return
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') setNavigationOpen(false) }
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [navigationOpen])
  const user = state.kind === 'user' ? state.user : null
  async function logout() {
    if (inFlight.current) return
    inFlight.current = true; setBusy(true); setError('')
    try { await accountApi.logout(); clear(); navigate('/login', { replace: true }) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Đăng xuất chưa hoàn tất.') }
    finally { inFlight.current = false; setBusy(false) }
  }
  const sectionTitle = location.pathname === '/reports' ? 'Báo cáo đã lưu' : location.pathname.includes('/projects') ? 'Dự án' : location.pathname.includes('/account') ? 'Tài khoản' : 'Tổng quan'
  return <div className={`workspace-shell${navigationOpen ? ' navigation-open' : ''}`}><aside id="workspace-navigation" className="workspace-sidebar">
    <Link className="brand" to="/app"><b className="brand-mark">SR</b><span>SmartRegression<small>Phân tích mã nguồn</small></span></Link>
    <nav aria-label="Điều hướng chính" onClick={() => setNavigationOpen(false)}>
      <NavLink to="/app" end><WorkspaceIcon name="overview" />Tổng quan</NavLink><NavLink to="/app/projects"><WorkspaceIcon name="projects" />Dự án</NavLink><NavLink to="/reports"><WorkspaceIcon name="reports" />Báo cáo đã lưu</NavLink><NavLink to="/app/account"><WorkspaceIcon name="account" />Tài khoản</NavLink>
    </nav><div className="sidebar-footer">{user ? <><div className="sidebar-person"><span className="avatar" aria-hidden="true">{user.display_name.slice(0, 1).toUpperCase()}</span>
      <div><strong>{user.display_name}</strong><small>{user.email}</small></div></div>
      <button disabled={busy} onClick={() => setConfirmLogout(true)}>{busy ? 'Đang đăng xuất…' : 'Đăng xuất'}</button></> : <><p>Đọc báo cáo trên máy mà không cần đăng nhập.</p><Link className="secondary-action" to="/login">Đăng nhập</Link></>}</div>
  </aside><div className="workspace-content"><header className="workspace-header"><div className="workspace-breadcrumb"><button type="button" className="navigation-toggle" aria-label={navigationOpen ? 'Đóng điều hướng' : 'Mở điều hướng'} aria-controls="workspace-navigation" aria-expanded={navigationOpen} onClick={() => setNavigationOpen(value => !value)}><WorkspaceIcon name={navigationOpen ? 'close' : 'menu'} /></button><span>Không gian cá nhân</span><span aria-hidden="true">/</span><strong>{sectionTitle}</strong></div>
    <div className="workspace-header-actions"><ThemeToggle /><span className="status-pill"><span className="status-dot" />{user ? user.verified ? 'Email đã xác thực' : 'Chờ xác thực email' : 'Chế độ đọc file'}</span></div></header>
    <main id="main-content" className="workspace-main">{error && <FormNotice error>{error}</FormNotice>}<div className="route-content" key={location.pathname}><Outlet /></div></main></div>
    <ConfirmDialog open={confirmLogout} title="Đăng xuất khỏi tài khoản?" confirmLabel="Đăng xuất" appearance="signout"
      onClose={() => setConfirmLogout(false)} onConfirm={() => { setConfirmLogout(false); void logout() }}>
      Bạn sẽ trở về trang đăng nhập. Chỉ phiên đăng nhập này kết thúc; bạn có thể quay lại bất cứ lúc nào.
    </ConfirmDialog></div>
}

function Home() {
  return <Dashboard />
}

function Profile() {
  const { state } = useAuth()
  return state.kind === 'user' ? <AccountView key={state.user.id} user={state.user} /> : null
}

function DemoRoute({ local }: { local: boolean | null }) {
  if (local === null) return <FormNotice>Đang kiểm tra chế độ demo…</FormNotice>
  if (!local) return <Navigate to="/login" replace />
  return <><nav className="demo-return"><Link to="/login">← Tài khoản SmartRegression</Link><span>DEMO LOCAL · không phải dữ liệu tài khoản</span></nav><LocalDemo /></>
}

export function ApplicationRoutes({ local }: { local: boolean | null }) {
  return <><a className="skip-link" href="#main-content">Bỏ qua đến nội dung</a><NavigationFocus /><Routes>
    <Route path="/" element={<Navigate to="/app" replace />} />
    <Route path="/login" element={<AuthForm key="login" kind="login" />} />
    <Route path="/register" element={<AuthForm key="register" kind="register" />} />
    <Route path="/forgot-password" element={<AuthForm key="forgot" kind="forgot" />} />
    <Route path="/verify-email" element={<AuthForm key="verify" kind="verify" />} />
    <Route path="/reset-password" element={<AuthForm key="reset" kind="reset" />} />
    <Route path="/check-email" element={<AuthForm key="check" kind="check" />} />
    <Route element={<Shell />}><Route path="/reports" element={<SavedReports />} /></Route>
    <Route element={<SessionGate />}><Route path="/app" element={<Shell />}>
      <Route element={<SessionGate verified />}><Route index element={<Home />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:projectId" element={<ProjectDetail />} />
        <Route path="projects/:projectId/runs/:runId" element={<RunDetail />} />
        <Route path="projects/:projectId/explorer" element={<Explorer />} />
        <Route path="projects/:projectId/what-if" element={<WhatIf />} />
        <Route path="projects/:projectId/scenarios/:scenarioId" element={<SavedScenario />} />
      </Route>
      <Route path="account" element={<Profile />} />
    </Route></Route>
    <Route path="/demo" element={<DemoRoute local={local} />} />
    <Route path="*" element={<main id="main-content"><h1>Không tìm thấy trang</h1><Link to="/">Về trang chính</Link></main>} />
  </Routes>{local && <Link className="local-demo-link" to="/demo">Mở demo local / báo cáo offline</Link>}</>
}

export function Application() {
  const [local, setLocal] = useState<boolean | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/v1/capabilities', { signal: controller.signal, cache: 'no-store' })
      .then(response => { if (!response.ok) throw new Error('Capabilities unavailable'); return response.json() })
      .then((data: unknown) => { if (!controller.signal.aborted) setLocal(typeof data === 'object' && data !== null && 'local_demo' in data && data.local_demo === true) })
      .catch(() => { if (!controller.signal.aborted) setLocal(import.meta.env.DEV && ['localhost', '127.0.0.1'].includes(window.location.hostname)) })
    return () => controller.abort()
  }, [])
  return <><ThemeController /><BrowserRouter><AuthProvider><ApplicationRoutes local={local} /></AuthProvider></BrowserRouter></>
}
