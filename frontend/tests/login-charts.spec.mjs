import { test, expect } from '@playwright/test'

for (const mode of ['light', 'dark']) {
  test(`login remains connected and usable at desktop/mobile in ${mode}`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: mode })
    await page.route('**/api/v1/**', route => new URL(route.request().url()).pathname.endsWith('/capabilities')
      ? route.fulfill({ json: { local_demo: false } }) : route.fulfill({ status: 401, json: { code: 'authentication_required' } }))
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: 'Chào mừng trở lại' })).toBeVisible()
    await expect(page.getByText('Sơ đồ minh hoạ', { exact: true })).toBeVisible()
    const panels = await page.locator('.auth-layout').evaluate(el => {
      const story = el.querySelector('.auth-story').getBoundingClientRect()
      const main = el.querySelector('.auth-main').getBoundingClientRect()
      return { gap: main.left - story.right, top: main.top - story.top, bottom: main.bottom - story.bottom }
    })
    expect(panels.gap).toBe(0)
    expect(panels.top).toBe(0)
    expect(panels.bottom).toBe(0)
    await page.getByLabel('Email', { exact: true }).fill('ui-fixture@example.com')
    await page.getByLabel('Mật khẩu', { exact: true }).fill('fixture-only-password')
    await page.getByRole('button', { name: 'Hiện mật khẩu', exact: true }).press('Enter')
    await expect(page.getByLabel('Mật khẩu', { exact: true })).toHaveAttribute('type', 'text')
    await page.getByRole('button', { name: 'Ẩn mật khẩu', exact: true }).press('Space')
    await expect(page.getByLabel('Mật khẩu', { exact: true })).toHaveAttribute('type', 'password')
    await page.getByRole('button', { name: `Chuyển sang giao diện ${mode === 'dark' ? 'sáng' : 'tối'}` }).click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', mode === 'dark' ? 'light' : 'dark')
    for (const width of [1440, 1024, 768, 375, 320]) {
      await page.setViewportSize({ width, height: 900 })
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `overflow at ${width}`).toBe(true)
      await expect(page.getByRole('button', { name: 'Đăng nhập', exact: true })).toBeVisible()
    }
    await page.getByRole('link', { name: 'Tạo tài khoản', exact: true }).click()
    await expect(page.getByLabel('Tên hiển thị')).toBeVisible()
    await expect(page.getByLabel('Nhập lại mật khẩu', { exact: true })).toBeVisible()
  })
}

test('login fits short desktop screens and centers its form without clipping the footer', async ({ page }) => {
  await page.route('**/api/v1/**', route => new URL(route.request().url()).pathname.endsWith('/capabilities')
    ? route.fulfill({ json: { local_demo: false } }) : route.fulfill({ status: 401, json: { code: 'authentication_required' } }))
  await page.goto('/login')
  for (const size of [{ width: 1440, height: 900 }, { width: 1366, height: 768 }, { width: 1280, height: 720 }, { width: 1280, height: 640 }]) {
    await page.setViewportSize(size)
    const layout = await page.evaluate(() => {
      const main = document.querySelector('.auth-main').getBoundingClientRect()
      const card = document.querySelector('.auth-main > .auth-card').getBoundingClientRect()
      const footer = document.querySelector('.auth-main-footer').getBoundingClientRect()
      const storyFooter = document.querySelector('.auth-story-footer').getBoundingClientRect()
      return { height: document.documentElement.scrollHeight, midpoint: (card.top + card.bottom) / 2 - (main.top + main.bottom) / 2, footerGap: footer.top - card.bottom, storyBottom: storyFooter.bottom }
    })
    expect(layout.height, `${size.width}×${size.height}`).toBeLessThanOrEqual(size.height + 1)
    expect(Math.abs(layout.midpoint)).toBeLessThan(2)
    expect(layout.footerGap).toBeGreaterThan(12)
    expect(layout.storyBottom).toBeLessThan(size.height)
  }
})

test('login exposes pending, credential error and connection error without replaying requests', async ({ page }) => {
  let pending
  let submissions = 0
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith('/auth/csrf')) return route.fulfill({ json: { token: 'fixture-csrf' } })
    if (path.endsWith('/auth/login')) { submissions++; pending = route; return }
    if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
    return route.fulfill({ status: 401, json: { code: 'authentication_required' } })
  })
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill('fixture@example.com')
  await page.getByLabel('Mật khẩu', { exact: true }).fill('fixture-only-password')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Đang xử lý…', exact: true })).toBeDisabled()
  await expect(page.locator('.auth-submit-spinner')).toBeVisible()
  await expect.poll(() => Boolean(pending)).toBe(true)
  await pending.fulfill({ status: 401, json: { code: 'invalid_credentials' } })
  await expect(page.getByRole('alert')).toHaveText('Email hoặc mật khẩu chưa đúng.')
  await expect(page.getByLabel('Mật khẩu', { exact: true })).toHaveAttribute('aria-invalid', 'true')
  await expect(page.getByLabel('Email', { exact: true })).toHaveAttribute('aria-describedby', 'auth-login-error')
  pending = null
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect.poll(() => Boolean(pending)).toBe(true)
  await pending.fulfill({ status: 503, json: { code: 'authentication_unavailable' } })
  await expect(page.getByRole('alert')).toContainText('Dịch vụ tài khoản')
  await expect(page.getByLabel('Mật khẩu', { exact: true })).not.toHaveAttribute('aria-invalid', 'true')
  expect(submissions).toBe(2)
})

test('login respects reduced motion and keeps focused inputs visible in both palettes', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: 'dark' })
  await page.route('**/api/v1/**', route => route.fulfill({ status: 401, json: { code: 'authentication_required' } }))
  await page.goto('/login')
  for (const mode of ['dark', 'light']) {
    await page.emulateMedia({ colorScheme: mode, reducedMotion: 'reduce' })
    await page.getByLabel('Email', { exact: true }).click()
    const styles = await page.getByLabel('Email', { exact: true }).evaluate(el => ({ radius: getComputedStyle(el).borderRadius, outline: getComputedStyle(el).outlineWidth }))
    expect(styles.radius).toBe('11px')
    expect(parseFloat(styles.outline)).toBeGreaterThan(0)
    expect(await page.locator('.auth-art-origin > rect').first().evaluate(el => getComputedStyle(el).animationName)).toBe('none')
  }
})

async function dashboardFixture(page, { empty = false, long = false } = {}) {
  const requests = []
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname
    requests.push(route.request().method())
    if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
    if (path.endsWith('/auth/me')) return route.fulfill({ json: { schema_version: '1.0.0', id: '11111111-1111-4111-8111-111111111111', email: 'fixture@example.com', display_name: 'Chart fixture · DEMO', verified: true } })
    if (path.endsWith('/projects') || path.endsWith('/runs') || path.endsWith('/usage')) return route.fulfill({ json: { items: [], next_cursor: null } })
    if (path.endsWith('/reporting/views/chart-fixture')) return route.fulfill({ json: {
      snapshot_id: 'chart-fixture', filters: { start: '2026-11-01T05:00:00Z', end: long ? '2026-12-01T05:00:00Z' : '2026-11-04T05:00:00Z', as_of: '2026-12-01T05:00:00Z', timezone: 'America/New_York', project_id: null, status: null },
      total_runs: empty ? 0 : 5, project_count: empty ? 0 : 1, known_actual_micro_usd: null, unknown_actual_count: 0, reservation_micro_usd: 0, stored_rows: 0, limitations: ['Fixture biểu đồ · DEMO'],
      daily_runs: empty ? {} : { '2026-11-01': 3, '2026-11-03': 2 }, static_statuses: empty ? {} : { completed: 3, failed: 2 }, ai_statuses: empty ? {} : { not_run: 4, completed: 1 },
    } })
    return route.fulfill({ status: 404, json: { code: 'not_found' } })
  })
  await page.goto('/app?view=chart-fixture')
  return requests
}

test('charts keep sparse calendar days, exact counts, percentages and AI state distinct', async ({ page }) => {
  const requests = await dashboardFixture(page)
  await expect(page.getByRole('heading', { name: 'Lượt phân tích theo ngày' })).toBeVisible()
  await expect(page.locator('.status-chart').filter({ hasText: 'Phân bố trạng thái tĩnh' })).toContainText('60%')
  await expect(page.locator('.status-chart').filter({ hasText: 'Trạng thái AI' })).toContainText('Chưa chạy')
  await page.getByText('Xem bảng số liệu', { exact: true }).click()
  const table = page.getByRole('table').filter({ hasText: 'Lượt phân tích theo ngày' })
  await expect(table.getByRole('row', { name: '2026-11-02 0', exact: true })).toBeVisible()
  await expect(table.getByRole('row', { name: '2026-11-04 0', exact: true })).toHaveCount(0)
  await page.getByRole('slider', { name: 'Xem từng ngày' }).press('Home')
  await expect(page.locator('.chart-readout')).toContainText('3 lượt phân tích')
  await page.getByRole('slider', { name: 'Xem từng ngày' }).press('ArrowRight')
  await expect(page.locator('.chart-readout')).toContainText('0 lượt phân tích')
  expect(requests.every(method => method === 'GET')).toBe(true)
})

test('long date ranges include DST and use a line without responsive overflow', async ({ page }) => {
  await dashboardFixture(page, { long: true })
  await page.getByText('Xem bảng số liệu', { exact: true }).click()
  const table = page.getByRole('table').filter({ hasText: 'Lượt phân tích theo ngày' })
  await expect(table.getByRole('row')).toHaveCount(31)
  await expect(page.locator('.chart-line')).toHaveCount(1)
  for (const mode of ['dark', 'light']) {
    await page.emulateMedia({ colorScheme: mode })
    for (const width of [1440, 768, 375]) {
      await page.setViewportSize({ width, height: 1000 })
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true)
    }
  }
})

test('empty snapshot shows no invented trend or status', async ({ page }) => {
  await dashboardFixture(page, { empty: true })
  await expect(page.getByText('Chưa có lượt phân tích trong khoảng thời gian này.')).toBeVisible()
  await expect(page.locator('.activity-plot')).toHaveCount(0)
  await expect(page.locator('.status-chart-list')).toHaveCount(0)
  await expect(page.locator('.chart-empty')).toHaveCount(3)
})
