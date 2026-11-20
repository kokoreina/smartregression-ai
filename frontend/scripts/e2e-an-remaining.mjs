// Owned native campaign only. Browser uses real HTTP/DB, without page.route mocks.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import path from 'node:path'
import { chromium, expect } from '@playwright/test'

const origin = process.env.SMARTREGRESSION_ACCEPTANCE_ORIGIN
assert(/^http:\/\/127\.0\.0\.1:\d+$/.test(origin ?? ''))
const folder = path.resolve(process.env.SMARTREGRESSION_ACCEPTANCE_DIR)
assert(folder.includes(path.join('var', 'tasks-352-360', 'browser-')))
const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
const page = await context.newPage()
page.setDefaultTimeout(15000)
page.setDefaultNavigationTimeout(60000)
const password = 'Synthetic acceptance password 2026!'
const email = `browser-${crypto.randomUUID()}@example.com`
const sha = 'b'.repeat(40)
const postCounts = { runs: 0, ai: 0 }
const errors = []
page.on('pageerror', error => errors.push(error.name))
page.on('request', request => {
  if (request.method() !== 'POST') return
  const path = new URL(request.url()).pathname
  if (/\/api\/v1\/projects\/[^/]+\/runs$/.test(path)) postCounts.runs++
  if (/\/api\/v1\/projects\/[^/]+\/(?:assistance\/ai|runs\/[^/]+\/ai)$/.test(path)) postCounts.ai++
})
async function mutate(ctx, suffix, data, method = 'POST') {
  const csrf = await (await ctx.request.get(origin + '/api/v1/auth/csrf')).json()
  return ctx.request.fetch(origin + '/api/v1' + suffix, { method, data, headers: { Origin: origin, 'X-CSRF-Token': csrf.token } })
}
async function login(target, value) {
  await target.goto(origin + '/login')
  await target.getByLabel('Email', { exact: true }).fill(value)
  await target.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await target.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await target.waitForURL('**/app')
}
async function download(button, filename) {
  const pending = page.waitForEvent('download')
  await button.click()
  const value = await pending
  await value.saveAs(path.join(folder, filename))
  return fs.readFile(path.join(folder, filename), 'utf8')
}
try {
  await page.goto(origin + '/register')
  await page.getByLabel('Tên hiển thị', { exact: true }).fill('Hà An · Kiểm thử riêng')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click()
  await page.waitForURL('**/check-email')
  const messages = JSON.parse(await fs.readFile(path.join(folder, 'synthetic-mailbox.json'), 'utf8'))
  const message = messages.findLast(item => item[0] === email && item[1] === 'verify')
  assert(message, 'synthetic verification captured')
  await page.goto(origin + '/verify-email#token=' + encodeURIComponent(message[2]))
  await page.getByRole('button', { name: 'Xác nhận email', exact: true }).click()
  await expect(page.getByText('Email đã được xác thực.', { exact: false })).toBeVisible()
  await login(page, email)
  await page.goto(origin + '/app/projects')
  await page.getByRole('button', { name: '+ Tạo dự án', exact: true }).click()
  await page.getByLabel('Tên dự án', { exact: true }).fill('Báo cáo kiểm chứng Hà An')
  await page.getByLabel('URL repo GitHub public', { exact: true }).fill('https://github.com/owner/repo')
  const created = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/api/v1/projects')
  await page.getByRole('button', { name: 'Tạo dự án', exact: true }).click()
  const project = (await (await created).json()).id
  const projectUrl = origin + '/app/projects/' + project
  await page.goto(projectUrl)
  await page.getByRole('button', { name: 'Mở phiên bản', exact: true }).click()
  await expect(page.getByText('Snapshot bbbbbbbb', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'app.py', exact: true }).first().click()
  await page.getByText('Ghi chú và ghim (0)', { exact: true }).click()
  await page.getByLabel('Tiêu đề ghi chú', { exact: true }).fill('Kiểm tra ảnh hưởng · tiếng Việt')
  await page.getByLabel('Nội dung ghi chú', { exact: true }).fill('<img src=x onerror=window.__xss=1> Nội dung là văn bản')
  await page.getByRole('button', { name: 'Lưu ghi chú / ghim', exact: true }).click()
  await expect(page.getByText('Kiểm tra ảnh hưởng · tiếng Việt', { exact: true })).toBeVisible()
  assert.equal(await page.evaluate(() => window.__xss), undefined)
  await expect.poll(async () => (await (await context.request.get(origin + `/api/v1/projects/${project}/view-state`)).json())?.path).toBe('app.py')
  await page.goto(projectUrl + '?tab=analysis')
  // Use the visible project tab rather than relying on undocumented query naming.
  await page.getByRole('button', { name: 'Phân tích & lịch sử', exact: true }).click()
  await page.getByLabel('Base SHA', { exact: true }).fill('a'.repeat(40))
  await page.getByLabel('Target SHA', { exact: true }).fill(sha)
  const started = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === `/api/v1/projects/${project}/runs`)
  await page.getByRole('button', { name: 'Phân tích tĩnh và lưu kết quả', exact: true }).click()
  const run = (await (await started).json()).id
  await expect.poll(async () => (await (await context.request.get(origin + `/api/v1/projects/${project}/runs/${run}`)).json()).status, { timeout: 30000 }).toBe('completed')
  const runUrl = projectUrl + '/runs/' + run
  await page.goto(runUrl)
  const exported = JSON.parse(await download(page.getByRole('button', { name: 'Tải báo cáo JSON đầy đủ', exact: true }), 'report.json'))
  assert.equal(exported.report_kind, 'saved-web-run')
  assert.equal(exported.payload.run.id, run)
  assert.equal(exported.payload.payload.report.identity.target.commit, sha)
  assert.equal(exported.ai_requests.length, 0)
  assert(!JSON.stringify(exported).includes(password))
  await page.goto(origin + '/app')
  await page.getByRole('button', { name: 'Cập nhật tổng quan', exact: true }).click()
  await expect(page.locator('#dashboard-runs .screen-only tbody tr')).toHaveCount(1)
  const dashboardUrl = page.url()
  const view = new URL(dashboardUrl).searchParams.get('view')
  const summary = await (await context.request.get(origin + '/api/v1/reporting/views/' + view)).json()
  const csv = await download(page.getByRole('button', { name: 'Xuất toàn bộ CSV theo bộ lọc', exact: true }), 'runs.csv')
  const csvRows = csv.trim().split(/\r?\n/).length - 1
  assert.equal(csvRows, summary.total_runs)
  assert(csv.includes(run))
  // Suppress only the OS print dialog; actual app pagination and print CSS run.
  await page.evaluate(() => { window.print = () => { window.__printCalled = true } })
  await page.getByRole('button', { name: 'In / Lưu PDF', exact: true }).click()
  await expect.poll(() => page.evaluate(() => window.__printCalled)).toBe(true)
  await page.emulateMedia({ media: 'print' })
  await expect(page.locator('.workspace-sidebar')).toBeHidden()
  await expect(page.locator('#dashboard-runs .print-only tbody tr')).toHaveCount(1)
  await page.pdf({ path: path.join(folder, 'dashboard-a4.pdf'), format: 'A4', landscape: true, printBackground: true })
  await page.screenshot({ path: path.join(folder, 'print-preview.png'), fullPage: true })
  await page.emulateMedia({ media: 'screen' })
  const before = { ...postCounts }
  assert.equal(before.runs, 1, 'journey must create exactly one run')
  assert.equal(before.ai, 0, 'journey must not launch AI')
  await fs.writeFile(path.join(folder, 'restart-request'), '')
  await expect.poll(async () => fs.stat(path.join(folder, 'restart-done')).then(() => true).catch(() => false)).toBe(true)
  await page.reload()
  await expect(page.locator('#dashboard-runs .screen-only tbody tr')).toHaveCount(1)
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await page.getByRole('dialog', { name: 'Đăng xuất khỏi tài khoản?', exact: true }).getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await page.waitForURL('**/login')
  await login(page, email)
  await page.goto(projectUrl)
  await expect(page.locator('.selected-path')).toHaveText('app.py')
  await page.getByText('Ghi chú và ghim (1)', { exact: true }).click()
  await expect(page.getByText('Kiểm tra ảnh hưởng · tiếng Việt', { exact: true })).toBeVisible()
  await page.goto(runUrl)
  await expect(page.getByRole('heading', { name: 'Kết quả: owner/repo', exact: true })).toBeVisible()
  assert.deepEqual(postCounts, before, 'reopen must not POST another run or AI')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: path.join(folder, 'mobile-report.png'), fullPage: true })
  await fs.writeFile(path.join(folder, 'mobile-layout.json'), JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('body *')].filter(el => el.getBoundingClientRect().right > innerWidth + 1).map(el => ({ tag: el.tagName, cls: el.className, right: el.getBoundingClientRect().right, width: el.getBoundingClientRect().width })).slice(-30)), null, 2))
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
  await page.keyboard.press('Tab')
  assert.notEqual(await page.evaluate(() => document.activeElement.tagName), 'BODY')
  await page.screenshot({ path: path.join(folder, 'mobile-report.png'), fullPage: true })
  const stranger = await browser.newContext()
  const other = await stranger.newPage()
  const otherEmail = `other-${crypto.randomUUID()}@example.com`
  assert.equal((await mutate(stranger, '/auth/register', { email: otherEmail, password, display_name: 'Other account' })).status(), 202)
  const secondMail = JSON.parse(await fs.readFile(path.join(folder, 'synthetic-mailbox.json'), 'utf8')).findLast(item => item[0] === otherEmail)
  assert.equal((await mutate(stranger, '/auth/verify-email', { token: secondMail[2] })).status(), 200)
  await login(other, otherEmail)
  for (const suffix of ['', `/snapshots/${sha}/graph`, '/notes', '/view-state', `/runs/${run}/report`]) {
    assert.equal((await stranger.request.get(origin + '/api/v1/projects/' + project + suffix)).status(), 404)
  }
  assert.equal((await mutate(stranger, `/projects/${project}/runs/${run}/export`, {})).status(), 404)
  assert.equal((await stranger.request.get(origin + '/api/v1/reporting/views/' + view)).status(), 404)
  assert.equal((await mutate(stranger, `/reporting/views/${view}/csv`, {})).status(), 404)
  assert.equal((await context.request.post(origin + `/api/v1/projects/${project}/archive`, { data: { version: 1 }, headers: { Origin: origin } })).status(), 403)
  assert.deepEqual(errors, [])
  await fs.writeFile(path.join(folder, 'result.json'), JSON.stringify({ dashboard_runs: summary.total_runs, csv_rows: csvRows, restart_resume: true, cross_owner_blocked: true, provider_calls: 0, boundaries: 'Synthetic GitHub and captured email; real HTTP/auth/DB/parser/browser' }, null, 2))
  console.log('PASS: signup, verification, project, snapshot, note, static run, JSON/CSV/PDF, restart, mobile and ownership')
} finally {
  await browser.close()
}
