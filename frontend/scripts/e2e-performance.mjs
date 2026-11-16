// Real browser rendering observations against an explicitly synthetic large fixture.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'

const origin = 'https://localhost:8444'
const root = fileURLToPath(new URL('../../var/phase3-8/browser-performance/', import.meta.url))
await fs.mkdir(root, { recursive: true })
const browser = await chromium.launch({ executablePath: process.env.SMARTREGRESSION_TEST_CHROMIUM, headless: true })
const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1440, height: 1000 } })
const page = await context.newPage()
const errors = []
page.on('pageerror', error => errors.push(error.name))
async function post(path, data) {
  const csrf = await (await context.request.get(origin + '/api/v1/auth/csrf')).json()
  return context.request.post(origin + '/api/v1' + path, { data, headers: { Origin: origin, 'X-CSRF-Token': csrf.token } })
}
try {
  const email = `performance_${Date.now()}@example.com`
  const password = 'Synthetic performance password 2026!'
  assert.equal((await post('/auth/register', { email, password, display_name: 'Performance fixture' })).status(), 202)
  const inbox = await (await context.request.get(`${origin}/__test__/mail?email=${encodeURIComponent(email)}`, { headers: { 'X-Test-Inbox': 'synthetic-e2e-only' } })).json()
  await page.goto(inbox.messages.at(-1).body.trim())
  await page.getByRole('button', { name: 'Xác nhận email', exact: true }).click()
  await page.getByText('Email đã được xác thực.', { exact: false }).waitFor()
  assert.equal((await post('/auth/login', { email, password })).status(), 200)
  const created = await post('/projects', { title: 'Synthetic 150 node performance', repository_url: 'https://github.com/owner/repo' })
  assert.equal(created.status(), 201)
  const project = await created.json()
  await page.goto(`${origin}/app/projects/${project.id}/explorer`)
  await page.getByLabel('Commit SHA đầy đủ', { exact: true }).fill('b'.repeat(40))
  const started = performance.now()
  await page.getByRole('button', { name: 'Tải snapshot và graph', exact: true }).click()
  await page.locator('.explorer-canvas .react-flow__node').nth(149).waitFor({ timeout: 30000 })
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
  const coldRenderMs = performance.now() - started
  assert.equal(await page.locator('.explorer-canvas .react-flow__node').count(), 150)
  const device = await page.evaluate(() => ({ userAgent: navigator.userAgent, hardwareConcurrency: navigator.hardwareConcurrency, memory: performance.memory ? { usedJSHeapSize: performance.memory.usedJSHeapSize, totalJSHeapSize: performance.memory.totalJSHeapSize } : null }))
  const currentUrl = page.url()
  const warmStart = performance.now()
  await page.reload()
  await page.locator('.explorer-canvas .react-flow__node').nth(149).waitFor()
  const warmRenderMs = performance.now() - warmStart
  await page.emulateMedia({ reducedMotion: 'reduce' })
  const maximumAnimationMs = await page.evaluate(() => Math.max(0, ...document.getAnimations().filter(item => item.playState === 'running').map(item => Number(item.effect?.getComputedTiming().duration) || 0)))
  assert(maximumAnimationMs <= 1, 'Reduced motion has no unnecessary running animation')
  await page.setViewportSize({ width: 768, height: 1000 })
  await page.evaluate(() => { document.documentElement.style.fontSize = '200%' })
  await page.getByRole('button', { name: 'Chi tiết', exact: true }).click()
  assert(!(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2)), '200% text zoom reflows at 768px')
  await page.screenshot({ path: root + 'zoom-200-768.png', fullPage: true })
  await page.evaluate(() => { document.documentElement.style.fontSize = '' })
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto(currentUrl)
  await page.screenshot({ path: root + 'graph-150.png', fullPage: true })
  assert.equal(errors.length, 0)
  await fs.writeFile(root + 'result.json', JSON.stringify({ passed: true, scope: '80 extra synthetic JS modules; 150-node canvas cap; no runtime execution or accuracy benchmark', browser: browser.version(), device, cold_acquisition_and_render_ms: coldRenderMs, cached_reload_render_ms: warmRenderMs, memory_limitations: 'JS heap sampled after render; not peak RSS, excludes browser/native memory', rendered_nodes: 150, reduced_motion_max_running_ms: maximumAnimationMs, text_zoom_200_percent: true, page_errors: errors }, null, 2))
  console.log(JSON.stringify({ passed: true, artifact: root + 'result.json' }))
} finally { await browser.close() }
