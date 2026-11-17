// Independent contexts, actual local SMTP + PostgreSQL; synthetic accounts only.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'

const origin = process.env.SMARTREGRESSION_E2E_ORIGIN ?? 'http://127.0.0.1:8150'
assert(['http://127.0.0.1:8150', 'https://localhost:8444'].includes(origin))
const root = fileURLToPath(new URL('../../var/phase3-8/security-browser' + (origin.startsWith('https:') ? '-https' : ''), import.meta.url))
await fs.mkdir(root, { recursive: true })
const browser = await chromium.launch({ executablePath: process.env.SMARTREGRESSION_TEST_CHROMIUM, headless: true, downloadsPath: root })
const contexts = []
const checks = []
const errors = []
const password = 'Synthetic initial password 2026!'
const resetPassword = 'Synthetic reset password 2026!'
const changedPassword = 'Synthetic changed password 2026!'
async function context() {
  const context = await browser.newContext({ ignoreHTTPSErrors: origin.startsWith('https:'), viewport: { width: 1440, height: 1000 } })
  contexts.push(context)
  const page = await context.newPage()
  page.on('pageerror', error => errors.push(error.name))
  return { context, page }
}
async function mutate(context, url, data, method = 'POST', extra = {}) {
  const response = await context.request.get(origin + '/api/v1/auth/csrf')
  const csrf = await response.json()
  return context.request.fetch(origin + '/api/v1' + url, { method, data, headers: { Origin: origin, 'X-CSRF-Token': csrf.token, ...extra } })
}
async function mail(context, email, purpose) {
  const deadline = Date.now() + 10000
  while (Date.now() < deadline) {
    const response = await context.request.get(`${origin}/__test__/mail?email=${encodeURIComponent(email)}`, { headers: { 'X-Test-Inbox': 'synthetic-e2e-only' } })
    const inbox = await response.json()
    const message = inbox.messages.findLast(item => item.body.includes('/' + purpose + '#token='))
    if (message) return message.body.trim()
    await new Promise(resolve => setTimeout(resolve, 200))
  }
  throw new Error('Actual local SMTP did not deliver expected message')
}
async function signup(page, email) {
  await page.goto(origin + '/register')
  await page.getByLabel('Tên hiển thị', { exact: true }).fill('Synthetic security account')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click()
  await page.waitForURL('**/check-email')
}
async function verify(context, page, email) {
  await page.goto(await mail(context, email, 'verify-email'))
  await page.getByRole('button', { name: 'Xác nhận email', exact: true }).click()
  await page.getByText('Email đã được xác thực.', { exact: false }).waitFor()
}
async function login(page, email, value = password) {
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.goto(origin + '/login')
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Mật khẩu', { exact: true }).fill(value)
    const pending = page.waitForResponse(response => response.url() === origin + '/api/v1/auth/login' && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
    const response = await pending
    if (response.status() !== 429) { assert.equal(response.status(), 200); return }
    const seconds = Number(response.headers()['retry-after'])
    assert(seconds > 0 && seconds <= 60, 'Rate limit provides bounded Retry-After')
    checks.push('login rate limit returned 429/Retry-After; test waited before explicit resubmit')
    await new Promise(resolve => setTimeout(resolve, (seconds + 1) * 1000))
  }
  throw new Error('Login remained rate limited after Retry-After')
}
try {
  const a = await context(); const b = await context(); const otherA = await context(); const guest = await context()
  const emailA = `security_a_${Date.now()}@example.com`; const emailB = `security_b_${Date.now()}@example.com`
  await signup(a.page, emailA)
  await login(a.page, emailA)
  await a.page.waitForURL('**/check-email')
  assert.equal((await a.context.request.get(origin + '/api/v1/projects')).status(), 403)
  assert.equal((await guest.context.request.get(origin + '/api/v1/projects')).status(), 401)
  await verify(a.context, a.page, emailA)
  await a.page.goto(origin + '/app/projects')
  await a.page.getByRole('button', { name: '+ Tạo dự án', exact: true }).click()
  await a.page.getByLabel('Tên dự án', { exact: true }).fill('Private synthetic project A')
  await a.page.getByLabel('URL repo GitHub public', { exact: true }).fill('https://github.com/owner/repo')
  await a.page.getByRole('button', { name: 'Tạo dự án', exact: true }).click()
  await a.page.getByRole('link', { name: 'Private synthetic project A', exact: true }).click()
  const project = a.page.url().split('/').at(-1)
  checks.push('guest 401; unverified 403; actual SMTP verification unlocks personal project')

  await signup(b.page, emailB); await verify(b.context, b.page, emailB); await login(b.page, emailB); await b.page.waitForURL('**/app')
  const sha = 'b'.repeat(40)
  const guessed = '00000000-0000-4000-8000-000000000001'
  const paths = ['', '/activity', '/repository', '/runs', `/runs/${guessed}`, `/runs/${guessed}/report`, `/runs/${guessed}/ai/${guessed}`, '/notes', '/scenarios', `/scenarios/${guessed}`, `/scenarios/${guessed}/graph`, `/scenarios/${guessed}/source`, `/snapshots/${sha}/graph`, `/snapshots/${sha}/source?path=payment.js`, `/snapshots/${sha}/tree`, `/snapshots/${sha}/impact?path=payment.js`, `/snapshots/${sha}/hotspots`, `/snapshots/${sha}/nodes`, `/snapshots/${sha}/calls?node=abc`, `/snapshots/${sha}/reading-guide`, '/view-state', `/assistance/ai?commit=${sha}`]
  for (const suffix of paths) assert.equal((await b.context.request.get(origin + '/api/v1/projects/' + project + suffix)).status(), 404, 'Cross-owner route ' + suffix)
  for (const suffix of [`/runs/${guessed}/export`, `/scenarios/${guessed}/export`]) assert.equal((await mutate(b.context, '/projects/' + project + suffix, {})).status(), 404)
  assert.equal((await a.context.request.post(origin + '/api/v1/projects/' + project + '/archive', { data: { version: 1 }, headers: { Origin: origin } })).status(), 403)
  assert.equal((await mutate(a.context, '/projects/' + project + '/archive', { version: 1 }, 'POST', { Origin: 'https://invalid.example' })).status(), 403)
  assert.equal((await mutate(a.context, '/projects/' + project, { title: 'Spoof', version: 1, owner_id: guessed }, 'PATCH')).status(), 422)
  checks.push('22 cross-owner reads and both exports return 404; missing CSRF/bad Origin/owner spoof rejected')

  await login(otherA.page, emailA); await otherA.page.waitForURL('**/app')
  await guest.page.goto(origin + '/forgot-password')
  await guest.page.getByLabel('Email', { exact: true }).fill(emailA)
  await guest.page.getByRole('button', { name: 'Yêu cầu liên kết khôi phục', exact: true }).click()
  const resetLink = await mail(guest.context, emailA, 'reset-password')
  await guest.page.goto(resetLink)
  await guest.page.getByLabel('Mật khẩu', { exact: true }).fill(resetPassword)
  await guest.page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(resetPassword)
  await guest.page.getByRole('button', { name: 'Đặt lại mật khẩu', exact: true }).click()
  await guest.page.getByText('Mật khẩu đã đổi. Hãy đăng nhập lại.', { exact: true }).waitFor()
  assert.equal((await a.context.request.get(origin + '/api/v1/auth/me')).status(), 401)
  assert.equal((await otherA.context.request.get(origin + '/api/v1/auth/me')).status(), 401)
  assert.equal((await b.context.request.get(origin + '/api/v1/auth/me')).status(), 200)
  checks.push('reset through SMTP/UI revokes both old A sessions while B remains signed in')

  await a.page.goto(origin + '/login'); await login(a.page, emailA, resetPassword); await a.page.waitForURL('**/app')
  await a.page.goto(origin + '/app/account')
  await a.page.getByLabel('Mật khẩu hiện tại', { exact: true }).fill(resetPassword)
  await a.page.getByLabel('Mật khẩu mới', { exact: true }).fill(changedPassword)
  await a.page.getByLabel('Nhập lại mật khẩu mới', { exact: true }).fill(changedPassword)
  await a.page.getByRole('button', { name: 'Đổi mật khẩu', exact: true }).click()
  await a.page.waitForURL('**/login')
  await login(a.page, emailA, changedPassword); await a.page.waitForURL('**/app')
  await a.page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await a.page.getByRole('dialog').getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await a.page.waitForURL('**/login')
  assert.equal((await a.context.request.get(origin + '/api/v1/auth/me')).status(), 401)
  checks.push('new password login -> change password revokes session -> fresh login -> logout and old cookie rejected')
  assert.equal(errors.length, 0)
  await fs.writeFile(path.join(root, 'result.json'), JSON.stringify({ passed: true, checks, page_errors: errors, scope: 'real browser/PostgreSQL/local SMTP; synthetic accounts; not Gmail/public TLS' }, null, 2))
  console.log(JSON.stringify({ passed: true, checks: checks.length, artifact: path.join(root, 'result.json') }))
} catch (error) {
  await fs.writeFile(path.join(root, 'result.json'), JSON.stringify({ passed: false, checks, error_type: error.name, page_errors: errors }, null, 2))
  throw error
} finally { for (const context of contexts) await context.close(); await browser.close() }
