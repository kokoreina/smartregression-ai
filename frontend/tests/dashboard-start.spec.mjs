import { test, expect } from '@playwright/test'

for (const state of ['ready', 'empty', 'unavailable']) {
  test(`dashboard start uses actual project response: ${state}`, async ({ page }) => {
    const requests = []
    await page.route('**/api/v1/**', route => {
      const request = route.request()
      const url = new URL(request.url())
      requests.push({ method: request.method(), path: url.pathname })
      const summary = { snapshot_id: 'chart-view', total_runs: 0, project_count: 0, known_actual_micro_usd: null, unknown_actual_count: 0, reservation_micro_usd: 0, stored_rows: 0, daily_runs: {}, static_statuses: {}, ai_statuses: {}, limitations: [], filters: { start: '2026-11-01T00:00:00Z', end: '2026-11-17T00:00:00Z', as_of: '2026-11-17T00:00:00Z', timezone: 'Asia/Ho_Chi_Minh' } }
      if (url.pathname === '/api/v1/reporting/views' || url.pathname === '/api/v1/reporting/views/chart-view') return route.fulfill({ json: summary })
      if (url.pathname.startsWith('/api/v1/reporting/views/chart-view/')) return route.fulfill({ json: { items: [], next_cursor: null } })
      if (url.pathname.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
      if (url.pathname.endsWith('/auth/csrf')) return route.fulfill({ json: { token: 'fixture-csrf-token' } })
      if (url.pathname.endsWith('/auth/me')) return route.fulfill({ json: { schema_version: '1.0.0', id: '11111111-1111-4111-8111-111111111111', email: 'fixture@example.com', display_name: 'Kiểm thử UI · DEMO', verified: true } })
      if (url.pathname === '/api/v1/projects') return state === 'unavailable'
        ? route.fulfill({ status: 503, json: { code: 'project_storage_unavailable' } })
        : route.fulfill({ json: { items: state === 'ready' && url.searchParams.get('archived') === 'false' ? [{ schema_version: '1.0.0', id: '11111111-1111-4111-8111-111111111111', title: 'Dự án từ API · DEMO', description: '', repository_url: 'https://github.com/example/project', archived: false, version: 1, created_at: '2026-11-17T00:00:00Z', updated_at: '2026-11-17T00:00:00Z' }] : [], next_cursor: null } })
      return route.fulfill({ status: 404, json: { code: 'not_found' } })
    })
    await page.goto('/app')
    await expect(page.getByRole('heading', { name: 'Tiếp tục với dự án' })).toBeVisible()
    if (state === 'ready') await expect(page.getByRole('link', { name: 'Dự án từ API · DEMO example/project' })).toBeVisible()
    if (state === 'empty') await expect(page.getByText('Chưa có dự án đang hoạt động.')).toBeVisible()
    if (state === 'unavailable') {
      await expect(page.getByText('Chưa đọc được danh sách dự án.', { exact: false })).toBeVisible()
      await expect(page.getByText('Chưa có dự án đang hoạt động.')).toHaveCount(0)
    }
    await expect(page.getByRole('link', { name: 'Mở báo cáo đã lưu' })).toHaveAttribute('href', '/reports')
    await expect(page.locator('.dashboard-kpis')).toHaveCount(0)
    expect(requests.some(request => request.method === 'POST')).toBe(false)
    for (const width of [1440, 1024, 768, 375]) {
      await page.setViewportSize({ width, height: 1000 })
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `dashboard overflow at ${width}px`).toBe(true)
    }
    if (state === 'ready') {
      await page.getByRole('button', { name: 'Xem biểu đồ', exact: true }).click()
      await expect(page.getByRole('heading', { name: 'Lượt phân tích theo ngày', exact: true })).toBeVisible()
      await expect(page.getByText('Chưa có lượt phân tích trong khoảng thời gian này.')).toBeVisible()
      expect(requests.filter(request => request.method === 'POST').map(request => request.path)).toEqual(['/api/v1/reporting/views'])
    }
  })
}
