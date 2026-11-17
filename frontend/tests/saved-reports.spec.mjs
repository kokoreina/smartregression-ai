import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

async function session(page, signedIn = false) {
  const requests = []
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname
    requests.push(path)
    if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
    if (path.endsWith('/auth/me')) return route.fulfill(signedIn
      ? { json: { schema_version: '1.0.0', id: '11111111-1111-4111-8111-111111111111', email: 'fixture@example.com', display_name: 'Kiểm thử UI · DEMO', verified: true } }
      : { status: 401, json: { code: 'authentication_required' } })
    return route.fulfill({ status: 404, json: { code: 'not_found' } })
  })
  await page.goto('/reports')
  return requests
}

test('reports stay available signed out and use the shared navigation', async ({ page }) => {
  await session(page)
  await expect(page.getByRole('heading', { level: 1, name: 'Báo cáo đã lưu' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Đăng nhập', exact: true })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Điều hướng chính' }).getByRole('link', { name: 'Báo cáo đã lưu', exact: true })).toHaveAttribute('aria-current', 'page')
  await page.getByRole('button', { name: 'Chọn file JSON', exact: true }).focus()
  const chooser = page.waitForEvent('filechooser')
  await page.keyboard.press('Enter')
  expect((await chooser).isMultiple()).toBe(false)
})

test('a local stage report opens and downloads its exact original bytes without analysis calls', async ({ page }) => {
  const requests = await session(page)
  const bytes = await readFile(new URL('../../examples/reports/stage-report.partial.json', import.meta.url))
  await page.getByLabel('Chọn báo cáo JSON').setInputFiles({ name: 'bao-cao-demo.json', mimeType: 'application/json', buffer: bytes })
  await expect(page.locator('.report-open-identity')).toContainText('bao-cao-demo.json')
  await expect(page.locator('.saved-report-content')).toContainText('DEMO')
  await expect(page.locator('.report-import-panel')).toHaveCount(0)
  const downloadEvent = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Tải JSON gốc', exact: true }).click()
  const download = await downloadEvent
  expect(download.suggestedFilename()).toBe('bao-cao-demo.json')
  expect(await readFile(await download.path())).toEqual(bytes)
  expect(requests.every(path => path.endsWith('/auth/me') || path.endsWith('/capabilities'))).toBe(true)
})

test('invalid replacement clears the previous report and gives one concise error', async ({ page }) => {
  await session(page)
  await page.getByLabel('Chọn báo cáo JSON').setInputFiles(fileURLToPath(new URL('../../examples/reports/stage-report.empty.json', import.meta.url)))
  await expect(page.locator('.saved-report-content')).toBeVisible()
  await page.getByLabel('Chọn báo cáo JSON').setInputFiles({ name: 'invalid.json', mimeType: 'application/json', buffer: Buffer.from('not json') })
  await expect(page.getByRole('alert')).toContainText('Không đọc được file JSON hợp lệ.')
  await expect(page.locator('.saved-report-content')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Chọn file JSON', exact: true })).toBeEnabled()
})

test('oversized files are rejected before parsing', async ({ page }) => {
  await session(page)
  await page.getByLabel('Chọn báo cáo JSON').setInputFiles({ name: 'large.json', mimeType: 'application/json', buffer: Buffer.alloc(16 * 1024 * 1024 + 1, ' ') })
  await expect(page.getByRole('alert')).toContainText('Báo cáo vượt giới hạn 16 MiB.')
  await expect(page.locator('.saved-report-content')).toHaveCount(0)
})

test('dropping a report uses the same validator and rejects multiple files', async ({ page }) => {
  await session(page)
  const content = await readFile(new URL('../../examples/reports/stage-report.partial.json', import.meta.url), 'utf8')
  const transfer = await page.evaluateHandle(content => {
    const data = new DataTransfer()
    data.items.add(new File([content], 'dropped-demo.json', { type: 'application/json' }))
    return data
  }, content)
  await page.getByRole('region', { name: 'Vùng mở báo cáo' }).dispatchEvent('drop', { dataTransfer: transfer })
  await expect(page.locator('.report-open-identity')).toContainText('dropped-demo.json')
  await expect(page.locator('.saved-report-content')).toContainText('DEMO')
  await page.reload()
  const multiple = await page.evaluateHandle(() => {
    const data = new DataTransfer()
    data.items.add(new File(['{}'], 'one.json'))
    data.items.add(new File(['{}'], 'two.json'))
    return data
  })
  await page.getByRole('region', { name: 'Vùng mở báo cáo' }).dispatchEvent('drop', { dataTransfer: multiple })
  await expect(page.getByRole('alert')).toContainText('Mỗi lần chỉ mở một file báo cáo.')
  await expect(page.locator('.saved-report-content')).toHaveCount(0)
})

test('scenario hypotheses remain visibly separate from measured impact', async ({ page }) => {
  await session(page)
  const value = { report_kind: 'saved-scenario', schema_version: '1.0.0', exported_at: '2026-11-17T00:00:00Z', ai_requests: [], payload: { schema_version: '1.0.0', id: 'demo', title: 'Kịch bản kiểm thử · DEMO', baseline: 'a'.repeat(40), path: 'app.py', mode: 'description', input: 'Giả thuyết kiểm thử giao diện.', created_at: '2026-11-17T00:00:00Z', impact: null, graph: null, delta: null, limitations: ['Dữ liệu DEMO phục vụ kiểm thử.'] } }
  await page.getByLabel('Chọn báo cáo JSON').setInputFiles({ name: 'scenario.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(value)) })
  await expect(page.locator('.saved-report-content')).toContainText('GIẢ THUYẾT')
  await expect(page.locator('.saved-report-content')).toContainText('Chưa có số liệu static.')
})

test('reports reflow at five widths and app labels contain no duplicate translations', async ({ page }) => {
  await session(page, true)
  await expect(page.getByRole('button', { name: 'Đăng xuất', exact: true })).toHaveCount(1)
  await expect(page.getByRole('button', { name: 'Đăng xuất', exact: true })).toHaveText('Đăng xuất')
  await expect(page.locator('html')).toHaveAttribute('lang', 'vi')
  await expect(page.locator('html')).toHaveAttribute('translate', 'no')
  await expect(page.locator('meta[name=google]')).toHaveAttribute('content', 'notranslate')
  for (const width of [1440, 1280, 1024, 768, 375]) {
    await page.setViewportSize({ width, height: 900 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `reports overflow at ${width}px`).toBe(true)
    await page.screenshot({ path: `../var/uiux-playwright/reports-${width}.png`, fullPage: true })
  }
})
