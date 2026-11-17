import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { accountApi, type CurrentUser } from './authClient'
import { useAuth } from './authContext'

export function FormNotice({ error = false, children }: { error?: boolean; children: ReactNode }) {
  return <div className={`form-notice ${error ? 'is-error' : ''}`} role={error ? 'alert' : 'status'}>{children}</div>
}

export function PasswordField({ name = 'password', label = 'Mật khẩu', current = false, confirm = false }: {
  name?: string; label?: string; current?: boolean; confirm?: boolean
}) {
  const [visible, setVisible] = useState(false)
  return <div className="field"><label htmlFor={name}>{label}</label>
    <div className="password-field"><input id={name} name={name} type={visible ? 'text' : 'password'} required
      minLength={current ? 1 : 12} maxLength={128} autoComplete={current ? 'current-password' : 'new-password'}
      aria-describedby={current || confirm ? undefined : `${name}-hint`} />
      <button type="button" aria-label={`${visible ? 'Ẩn' : 'Hiện'} ${label.toLowerCase()}`}
        aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? 'Ẩn' : 'Hiện'}</button></div>
    {!current && !confirm && <small id={`${name}-hint`}>12–128 ký tự. Có thể dùng trình quản lý mật khẩu.</small>}
  </div>
}

export function SessionGate({ verified = false }: { verified?: boolean }) {
  const { state, refresh } = useAuth()
  if (state.kind === 'loading') return <FormNotice>Đang kiểm tra phiên đăng nhập…</FormNotice>
  if (state.kind === 'unavailable') return <div className="auth-card"><FormNotice error>{state.message}</FormNotice>
    <button onClick={() => void refresh()}>Thử kết nối lại</button><Link to="/login">Đến đăng nhập</Link></div>
  if (state.kind !== 'user') return <Navigate to="/login" replace />
  if (verified && !state.user.verified) return <Navigate to="/check-email" replace />
  return <Outlet />
}

export function AuthFrame({ children }: { children: ReactNode }) {
  return <div className="auth-layout"><section className="auth-story" aria-label="SmartRegression">
    <Link to="/" className="brand">SR<span>SmartRegression AI</span></Link>
    <p className="eyebrow">HIỂU REPO · HIỂU THAY ĐỔI</p>
    <h1>Mỗi thay đổi.<br />Một góc nhìn rõ hơn.</h1>
    <p>Khám phá cấu trúc, quan hệ phụ thuộc và bằng chứng phân tích trong một không gian làm việc.</p>
    <div className="story-lines" aria-hidden="true"><span>repository /</span><span>├── structure</span><span>├── dependencies</span><span>└── evidence</span></div>
  </section><main id="main-content" className="auth-main">{children}</main></div>
}

type Kind = 'login' | 'register' | 'forgot' | 'verify' | 'reset' | 'check'
const headings: Record<Kind, string> = { login: 'Chào mừng trở lại', register: 'Tạo tài khoản',
  forgot: 'Khôi phục mật khẩu', verify: 'Xác thực email', reset: 'Đặt mật khẩu mới', check: 'Kiểm tra hộp thư' }

export function AuthForm({ kind }: { kind: Kind }) {
  const { state, accept, refresh } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [token, setToken] = useState('')
  const inFlight = useRef(false)
  const active = useRef(true)
  const fragmentRead = useRef(false)
  useEffect(() => {
    active.current = true
    if (!fragmentRead.current && (kind === 'verify' || kind === 'reset')) {
      fragmentRead.current = true
      const value = new URLSearchParams(window.location.hash.slice(1)).get('token') ?? ''
      setToken(value.length <= 256 ? value : '')
      window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search)
    }
    return () => { active.current = false }
  }, [kind])

  if ((kind === 'login' || kind === 'register') && state.kind === 'user') {
    return <Navigate to={state.user.verified ? '/app' : '/check-email'} replace />
  }

  const userEmail = state.kind === 'user' ? state.user.email : ''
  const fromRegistration: unknown = location.state
  const email = userEmail || (typeof fromRegistration === 'object' && fromRegistration !== null
    && 'email' in fromRegistration && typeof fromRegistration.email === 'string' ? fromRegistration.email : '')
  const navigationMessage = typeof fromRegistration === 'object' && fromRegistration !== null
    && 'message' in fromRegistration && typeof fromRegistration.message === 'string' ? fromRegistration.message : ''

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (inFlight.current) return
    const form = event.currentTarget
    const data = new FormData(form)
    const value = (name: string) => String(data.get(name) ?? '')
    if ((kind === 'register' || kind === 'reset') && value('password') !== value('confirm')) {
      setError('Hai mật khẩu chưa khớp.'); form.querySelector<HTMLInputElement>('[name=confirm]')?.focus(); return
    }
    setError(''); setMessage(''); setBusy(true); inFlight.current = true
    try {
      if (kind === 'login') {
        const user = await accountApi.login({ email: value('email'), password: value('password') })
        if (!active.current) return
        accept(user); navigate(user.verified ? '/app' : '/check-email', { replace: true })
      } else if (kind === 'register') {
        await accountApi.register({ email: value('email'), password: value('password'), display_name: value('display_name') })
        if (active.current) navigate('/check-email', { replace: true, state: { email: value('email') } })
      } else {
        const result = kind === 'forgot' ? await accountApi.forgot({ email: value('email') })
          : kind === 'check' ? await accountApi.resend({ email: value('email') })
          : kind === 'verify' ? await accountApi.verify(token)
          : await accountApi.reset({ token, password: value('password') })
        if (!active.current) return
        setMessage(result.message)
        if (kind === 'verify' || kind === 'reset') { setToken(''); form.reset(); await refresh() }
      }
    } catch (cause) {
      if (active.current) setError(cause instanceof Error ? cause.message : 'Yêu cầu chưa hoàn tất.')
    } finally { inFlight.current = false; if (active.current) setBusy(false) }
  }

  const needsLink = kind === 'verify' || kind === 'reset'
  return <AuthFrame><section className="auth-card" aria-labelledby="auth-title">
    <p className="eyebrow">TÀI KHOẢN SMARTREGRESSION</p><h1 id="auth-title">{headings[kind]}</h1>
    {kind === 'check' && <p>Yêu cầu đã được tiếp nhận. Kiểm tra Inbox và Spam. Tài khoản chỉ được xác thực sau khi bạn xác nhận liên kết trong email.</p>}
    {kind === 'verify' && <p>Bấm xác nhận bên dưới để sử dụng liên kết. Việc mở trang chưa xác thực tài khoản.</p>}
    {kind === 'forgot' && <p>Nếu email phù hợp với tài khoản, hệ thống sẽ thử gửi liên kết khôi phục.</p>}
    {state.kind === 'unavailable' && <FormNotice error>{state.message}</FormNotice>}
    {navigationMessage && <FormNotice>{navigationMessage}</FormNotice>}
    {error && <FormNotice error>{error}</FormNotice>}{message && <FormNotice>{message}</FormNotice>}
    {needsLink && !token && !message && <FormNotice error>Không có liên kết hợp lệ. Hãy mở lại liên kết từ email hoặc yêu cầu email mới.</FormNotice>}
    <form className="account-form" onSubmit={submit} aria-busy={busy}>
      {kind === 'register' && <div className="field"><label htmlFor="display_name">Tên hiển thị</label><input id="display_name" name="display_name" required maxLength={80} autoComplete="name" /></div>}
      {!needsLink && <div className="field"><label htmlFor="email">Email</label><input key={email} id="email" name="email" type="email" defaultValue={email} required maxLength={254} autoComplete="username" readOnly={kind === 'check' && !!userEmail} /></div>}
      {(kind === 'login' || kind === 'register' || kind === 'reset') && <PasswordField current={kind === 'login'} />}
      {(kind === 'register' || kind === 'reset') && <PasswordField name="confirm" label="Nhập lại mật khẩu" confirm />}
      <button className="primary-button" disabled={busy || (needsLink && !token)} type="submit">
        {busy ? 'Đang xử lý…' : ({ login: 'Đăng nhập', register: 'Tạo tài khoản', forgot: 'Yêu cầu liên kết khôi phục', verify: 'Xác nhận email', reset: 'Đặt lại mật khẩu', check: 'Yêu cầu gửi lại email' })[kind]}
      </button>
    </form>
    <nav className="auth-links" aria-label="Liên kết tài khoản">
      {kind !== 'login' && <Link to="/login">Đăng nhập</Link>}
      {kind === 'login' && <><Link to="/register">Tạo tài khoản</Link><Link to="/forgot-password">Quên mật khẩu?</Link></>}
      {needsLink && <Link to={kind === 'reset' ? '/forgot-password' : '/check-email'}>Yêu cầu email mới</Link>}
      {kind === 'check' && state.kind === 'user' && <Link to="/app/account">Tài khoản</Link>}
    </nav>
  </section></AuthFrame>
}

export function AccountView({ user }: { user: CurrentUser }) {
  const { accept, clear } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const inFlight = useRef(false)
  const active = useRef(true)
  useEffect(() => { active.current = true; return () => { active.current = false } }, [])
  async function submit(event: FormEvent<HTMLFormElement>, password = false) {
    event.preventDefault()
    if (inFlight.current) return
    const form = event.currentTarget
    const data = new FormData(form)
    if (password && data.get('password') !== data.get('confirm')) { setError('Hai mật khẩu chưa khớp.'); return }
    setBusy(true); inFlight.current = true; setError(''); setMessage('')
    try {
      if (password) {
        const result = await accountApi.change({ current_password: String(data.get('current_password')), password: String(data.get('password')) })
        if (!active.current) return
        form.reset(); clear(); navigate('/login', { replace: true, state: { message: result.message } })
      } else {
        const updated = await accountApi.profile({ display_name: String(data.get('display_name')) })
        if (active.current) { accept(updated); setMessage('Đã cập nhật tên hiển thị.') }
      }
    } catch (cause) { if (active.current) setError(cause instanceof Error ? cause.message : 'Chưa cập nhật được.') }
    finally { inFlight.current = false; if (active.current) setBusy(false) }
  }
  return <section className="account-panel"><p className="eyebrow">KHÔNG GIAN CÁ NHÂN</p><h1>Tài khoản của bạn</h1>
    <p>{user.email} <span className={`status-pill ${user.verified ? 'verified' : ''}`}>{user.verified ? 'Đã xác thực' : 'Chưa xác thực'}</span></p>
    {!user.verified && <FormNotice>Hãy <Link to="/check-email">xác thực email</Link> trước khi sử dụng chức năng nghiệp vụ.</FormNotice>}
    {error && <FormNotice error>{error}</FormNotice>}{message && <FormNotice>{message}</FormNotice>}
    <form className="account-form auth-card" onSubmit={event => void submit(event)} aria-busy={busy}><h2>Thông tin cá nhân</h2>
      <div className="field"><label htmlFor="display_name">Tên hiển thị</label><input id="display_name" name="display_name" defaultValue={user.display_name} required maxLength={80} autoComplete="name" /></div>
      <button type="submit" className="primary-button" disabled={busy}>Lưu thông tin</button>
    </form>
    {user.verified && <form className="account-form auth-card" onSubmit={event => void submit(event, true)} aria-busy={busy}><h2>Đổi mật khẩu</h2>
      <PasswordField name="current_password" label="Mật khẩu hiện tại" current /><PasswordField label="Mật khẩu mới" /><PasswordField name="confirm" label="Nhập lại mật khẩu mới" confirm />
      <p className="muted">Sau khi đổi, tất cả phiên đăng nhập sẽ bị thu hồi.</p><button type="submit" disabled={busy}>Đổi mật khẩu</button>
    </form>}
  </section>
}
