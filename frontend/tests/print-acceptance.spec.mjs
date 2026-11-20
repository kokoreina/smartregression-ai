import { test, expect } from '@playwright/test'

test('print loads every frozen page and keeps Vietnamese provenance and final row', async ({ page }, info) => {
  const reads = []
  const usageReads = []
  const rows = Array.from({ length: 105 }, (_, index) => ({ id: `run-${String(index).padStart(8, '0')}`, project_id: 'project-fixture', base: 'a'.repeat(40), target: 'b'.repeat(40), status: 'completed', ai_status: 'not_run', started_at: '2026-11-19T00:00:00Z' }))
  const usageRows = Array.from({ length: 126 }, (_, index) => ({ id: `usage-${String(index).padStart(8, '0')}`, action: `explain-${index}`, status: 'completed', actual_micro_usd: 1000, reservation_micro_usd: 0 }))
  await page.route('**/api/v1/**', route => {
    const url = new URL(route.request().url()), path = url.pathname
    if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
    if (path.endsWith('/auth/me')) return route.fulfill({ json: { id: 'print-fixture', email: 'fixture@example.com', display_name: 'Print · DEMO', verified: true } })
    if (path.endsWith('/projects')) return route.fulfill({ json: { items: [], next_cursor: null } })
    if (path.endsWith('/usage')) {
      const start = Number(url.searchParams.get('offset') ?? 0), limit = Number(url.searchParams.get('limit') ?? 25)
      usageReads.push({ start, limit })
      return route.fulfill({ json: { items: usageRows.slice(start, start + limit), next_cursor: start + limit < usageRows.length ? 'more' : null } })
    }
    if (path.endsWith('/runs')) {
      const start = Number(url.searchParams.get('offset') ?? 0), limit = Number(url.searchParams.get('limit') ?? 25)
      reads.push({ start, limit })
      return route.fulfill({ json: { items: rows.slice(start, start + limit), next_cursor: start + limit < rows.length ? 'more' : null } })
    }
    if (path.endsWith('/reporting/views/print-fixture')) return route.fulfill({ json: {
      snapshot_id: 'print-fixture', filters: { start: '2026-11-01T00:00:00Z', end: '2026-11-19T00:00:00Z', as_of: '2026-11-19T00:00:00Z', timezone: 'Asia/Ho_Chi_Minh' },
      total_runs: 105, project_count: 1, daily_runs: { '2026-11-19': 105 }, static_statuses: { completed: 105 }, ai_statuses: { not_run: 105 }, stored_rows: 105,
      known_actual_micro_usd: null, unknown_actual_count: 0, reservation_micro_usd: 0, limitations: ['Giới hạn kiểm chứng · synthetic print fixture · DEMO'],
    } })
    return route.fulfill({ status: 404, json: { code: 'not_found' } })
  })
  await page.goto('/app?view=print-fixture')
  await expect(page.locator('#dashboard-runs .screen-only tbody tr')).toHaveCount(25)
  await page.evaluate(() => { window.print = () => { window.__printed = true } })
  await page.getByRole('button', { name: 'In / Lưu PDF', exact: true }).click()
  await expect.poll(() => page.evaluate(() => window.__printed)).toBe(true)
  expect(reads).toContainEqual({ start: 0, limit: 100 })
  expect(reads).toContainEqual({ start: 100, limit: 100 })
  expect(usageReads).toContainEqual({ start: 0, limit: 100 })
  expect(usageReads).toContainEqual({ start: 100, limit: 100 })
  await page.emulateMedia({ media: 'print' })
  await expect(page.locator('#dashboard-runs .print-only tbody tr')).toHaveCount(105)
  await expect(page.locator('#dashboard-runs .print-only tbody tr').last()).toContainText('run-00000104')
  await expect(page.locator('#dashboard-usage .print-only tbody tr')).toHaveCount(126)
  await expect(page.locator('#dashboard-usage .print-only tbody tr').last()).toContainText('explain-125')
  await expect(page.locator('.workspace-sidebar')).toBeHidden()
  await expect(page.locator('.report-provenance')).toContainText('Asia/Ho_Chi_Minh')
  await page.pdf({ path: info.outputPath('dashboard-105-rows-a4.pdf'), format: 'A4', landscape: true, printBackground: true })
})
