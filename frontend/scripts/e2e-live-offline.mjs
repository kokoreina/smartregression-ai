// Display real saved Gemini outputs without any new provider request or user login.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'
const root = fileURLToPath(new URL('../../var/phase3-8/live-ai/', import.meta.url))
const origin = 'http://127.0.0.1:5173'
const browser = await chromium.launch({ executablePath: process.env.SMARTREGRESSION_TEST_CHROMIUM, headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
const page = await context.newPage()
const errors = []
page.on('pageerror', error => errors.push(error.name))
try {
  await page.goto(origin + '/reports')
  await page.getByRole('heading', { name: 'Mở báo cáo đã lưu', exact: true }).waitFor()
  await page.waitForLoadState('networkidle')
  let requests = 0
  page.on('request', request => { if (request.url().includes('/api/')) requests++ })
  await context.setOffline(true)
  await page.getByLabel('Chọn báo cáo JSON', { exact: true }).setInputFiles(root + 'sqlparse-run.json')
  await page.getByRole('heading', { name: 'Kết quả: andialbrecht/sqlparse', exact: true }).waitFor()
  const reference = page.locator('.metadata-links a').first()
  await reference.waitFor()
  await reference.click()
  assert(await page.evaluate(() => document.activeElement?.id.startsWith('metadata-')))
  await page.screenshot({ path: root + 'saved-live-run-browser.png', fullPage: true })
  await page.getByLabel('Chọn báo cáo JSON', { exact: true }).setInputFiles(root + 'sqlparse-hypothesis.json')
  await page.getByRole('heading', { name: 'DEMO · Thêm bước kiểm tra đầu vào', exact: true }).waitFor()
  await page.getByRole('heading', { name: 'Gemini đã lưu', exact: true }).waitFor()
  assert.equal(requests, 0)
  assert.equal(errors.length, 0)
  await page.screenshot({ path: root + 'saved-live-hypothesis-browser.png', fullPage: true })
  await fs.writeFile(root + 'offline-browser.json', JSON.stringify({ passed: true, scope: 'real saved public sqlparse Gemini outputs; browser network disabled during imports; no new AI call', citations_keyboard_focus: true, api_requests_during_import: requests, page_errors: errors }, null, 2))
  console.log(JSON.stringify({ passed: true, artifact: root + 'offline-browser.json' }))
} finally { await browser.close() }
