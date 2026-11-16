/** Auth forms/contracts/transport checks. SSR is not browser acceptance. */
import assert from 'node:assert/strict'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import { MemoryRouter } from 'react-router-dom'

const root = new URL('../', import.meta.url)
const server = await createServer({ root: fileURLToPath(root), configFile: false,
  cacheDir: fileURLToPath(new URL('node_modules/.vite-auth-ssr', root)),
  optimizeDeps: { noDiscovery: true, include: [] },
  server: { middlewareMode: true, hmr: false, watch: null }, esbuild: { jsx: 'automatic' } })
const originalFetch = globalThis.fetch
const originalWindow = globalThis.window
let checks = 0
try {
  const { AuthForm, PasswordField, SessionGate, AccountView } = await server.ssrLoadModule('/src/features/auth/AuthViews.tsx')
  const { AuthContext } = await server.ssrLoadModule('/src/features/auth/authContext.ts')
  const { ApplicationRoutes } = await server.ssrLoadModule('/src/app/Application.tsx')
  const context = { state: { kind: 'guest' }, accept() {}, clear() {}, async refresh() {} }
  function view(component, state = context.state, url = '/login') {
    return renderToStaticMarkup(createElement(MemoryRouter, { initialEntries: [url] },
      createElement(AuthContext.Provider, { value: { ...context, state } }, component)))
  }
  for (const kind of ['login', 'register', 'forgot', 'verify', 'reset', 'check']) {
    const html = view(createElement(AuthForm, { kind }))
    assert(html.includes('<h1') && html.includes('<form') && html.includes('aria-busy="false"'))
    assert(!html.includes('localStorage'))
    checks++
  }
  assert(view(createElement(PasswordField)).includes('minLength="12"'))
  assert(view(createElement(PasswordField)).includes('autoComplete="new-password"'))
  assert(view(createElement(PasswordField, { current: true })).includes('autoComplete="current-password"'))
  const user = { schema_version: '1.0.0', id: 'a', email: 'huy@example.com', display_name: '<script>alert(1)</script>', verified: true }
  assert(view(createElement(AccountView, { user }), { kind: 'user', user }).includes('&lt;script&gt;'))
  assert(view(createElement(SessionGate), { kind: 'loading' }).includes('Đang kiểm tra phiên'))
  assert(!view(createElement(ApplicationRoutes, { local: false }), { kind: 'user', user }, '/app').includes('Mở demo local'))
  checks += 6
  const { accountApi, AccountError, clearAuthClient } = await server.ssrLoadModule('/src/features/auth/authClient.ts')
  const calls = []
  globalThis.window = { dispatchEvent() {} }
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options })
    if (url.endsWith('/csrf')) return new Response(JSON.stringify({ token: 'synthetic-csrf-token' }), { status: 200 })
    return new Response(JSON.stringify({ code: 'csrf_invalid', message: 'raw backend detail' }), { status: 403 })
  }
  clearAuthClient()
  await assert.rejects(accountApi.register({ email: 'huy@example.com', password: 'synthetic-password', display_name: 'Huy' }),
    error => error instanceof AccountError && error.code === 'csrf_invalid' && !error.message.includes('raw backend detail'))
  assert.equal(calls.filter(c => c.options.method === 'POST').length, 1, 'Never replay a rejected mutation')
  assert.equal(calls.filter(c => c.url.endsWith('/csrf')).length, 2, 'Refresh CSRF for manual retry')
  assert(calls.every(c => c.options.credentials === 'same-origin'))
  checks += 4
  let expired = 0
  globalThis.window = { dispatchEvent() { expired++ } }
  globalThis.fetch = async () => new Response(JSON.stringify({ code: 'authentication_required' }), { status: 401 })
  await assert.rejects(accountApi.me(), error => error instanceof AccountError && error.status === 401)
  assert.equal(expired, 1)
  checks += 2
  expired = 0
  clearAuthClient()
  globalThis.fetch = async url => url.endsWith('/csrf')
    ? new Response(JSON.stringify({ token: 'synthetic-csrf' }), { status: 200 })
    : new Response(JSON.stringify({ code: 'invalid_credentials' }), { status: 401 })
  await assert.rejects(accountApi.change({ current_password: 'wrong', password: 'new synthetic password' }),
    error => error instanceof AccountError && error.code === 'invalid_credentials')
  assert.equal(expired, 0, 'Wrong current password must not clear a valid session')
  checks++
  globalThis.fetch = async () => { throw new TypeError('private network detail') }
  await assert.rejects(accountApi.me(), error => !error.message.includes('private network detail') && error.message.includes('API'))
  checks++
  console.log(`${checks} auth UI/transport checks passed (SSR, not browser)`)
} finally {
  globalThis.fetch = originalFetch
  globalThis.window = originalWindow
  await server.close()
}
