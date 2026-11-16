// Observe the actual restarted primary and Compose apps, using no user credentials.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'
const browser = await chromium.launch({ executablePath: process.env.SMARTREGRESSION_TEST_CHROMIUM, headless: true })
const checks = []
try {
  for (const origin of ['http://127.0.0.1:5173', 'https://localhost:8443']) {
    const context = await browser.newContext({ ignoreHTTPSErrors: origin.startsWith('https:') })
    const page = await context.newPage()
    const errors = []
    page.on('pageerror', error => errors.push(error.name))
    await page.goto(origin + '/login')
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).waitFor()
    const capability = await (await context.request.get(origin + '/api/v1/capabilities')).json()
    assert.equal(capability.local_demo, false)
    assert.equal((await context.request.post(origin + '/api/repository-analyses', { data: {} })).status(), 404)
    await page.reload()
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).waitFor()
    await page.goto(origin + '/reports')
    await page.getByText('Mở báo cáo đã lưu', { exact: false }).first().waitFor()
    assert.deepEqual(errors, [])
    checks.push({ origin, login_reload_offline_reader: true, product_legacy_post_isolated: true })
    await context.close()
  }
  const result = fileURLToPath(new URL('../../var/phase3-8/restarted-app-browser.json', import.meta.url))
  await fs.writeFile(result, JSON.stringify({ passed: true, checks, scope: 'dedicated real browser; no login or provider call; certificate exception for local Compose only' }, null, 2))
  console.log(JSON.stringify({ passed: true, checks: checks.length, artifact: result }))
} finally { await browser.close() }
