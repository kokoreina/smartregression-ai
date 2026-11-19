import { test, expect } from '@playwright/test'

for (const known of [null, 0, 25]) {
  test(`usage preserves unknown, zero and known costs separately: ${known}`, async ({ page }) => {
    const requests = []
    await page.route('**/api/v1/**', route => {
      const req = route.request(), path = new URL(req.url()).pathname
      requests.push(req.method())
      if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
      if (path.endsWith('/auth/me')) return route.fulfill({ json: { id: '11111111-1111-4111-8111-111111111111', email: 'fixture@example.com', display_name: 'Usage · DEMO', verified: true } })
      if (path.endsWith('/projects') || path.endsWith('/runs')) return route.fulfill({ json: { items: [], next_cursor: null } })
      if (path.endsWith('/reporting/views/usage-fixture')) return route.fulfill({ json: {
        snapshot_id: 'usage-fixture', filters: { start: '2026-11-01T00:00:00Z', end: '2026-11-19T00:00:00Z', as_of: '2026-11-19T00:00:00Z', timezone: 'UTC' },
        total_runs: 0, project_count: 0, daily_runs: {}, static_statuses: {}, ai_statuses: {}, stored_rows: 0,
        known_actual_micro_usd: known, unknown_actual_count: 1, reservation_micro_usd: 20000, limitations: ['Synthetic usage fixture · DEMO'],
      } })
      if (path.endsWith('/usage')) return route.fulfill({ json: { items: [null, 0, 25].map((cost, index) => ({ id: `fixture-${index}`, action: 'file', status: 'failed', actual_micro_usd: cost, reservation_micro_usd: 20000 })), next_cursor: null } })
      return route.fulfill({ status: 404, json: { code: 'not_found' } })
    })
    await page.goto('/app?view=usage-fixture')
    const cost = page.locator('.dashboard-kpis a').filter({ hasText: 'Chi phí đã biết' })
    await expect(cost.locator('strong')).toHaveText(known === null ? 'N/A' : (known / 1e6).toFixed(6))
    await expect(page.getByText('Khoản giữ chỗ chưa quyết toán: 0.020000 USD. Đây không phải chi phí thực tế.', { exact: true })).toBeVisible()
    const table = page.locator('#dashboard-usage')
    await expect(table.getByRole('cell', { name: 'Chưa biết', exact: true })).toHaveCount(1)
    await expect(table.getByRole('cell', { name: '0.000000 USD', exact: true })).toHaveCount(1)
    await expect(table.getByRole('cell', { name: '0.000025 USD', exact: true })).toHaveCount(1)
    expect(requests.every(method => method === 'GET')).toBe(true)
  })
}
