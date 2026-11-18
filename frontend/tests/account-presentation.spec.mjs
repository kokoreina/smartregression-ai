import { test, expect } from '@playwright/test'

async function accountFixture(page) {
  const logout = []
  let authenticated = true
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
    if (path.endsWith('/auth/csrf')) return route.fulfill({ json: { token: 'fixture-csrf-token' } })
    if (path.endsWith('/auth/logout')) {
      logout.push(route.request().method()); authenticated = false
      return route.fulfill({ json: { schema_version: '1.0.0', message: 'Đã đăng xuất.' } })
    }
    if (path.endsWith('/auth/me') && authenticated) return route.fulfill({ json: { schema_version: '1.0.0', id: '11111111-1111-4111-8111-111111111111', email: 'fixture@example.com', display_name: 'Tài khoản kiểm thử · DEMO', verified: true } })
    return route.fulfill({ status: 401, json: { code: 'authentication_required' } })
  })
  await page.goto('/app/account')
  await expect(page.getByRole('heading', { name: 'Tài khoản của bạn' })).toBeVisible()
  return logout
}

test('account verification uses readable themed colors without a bright dark-mode badge', async ({ page }) => {
  await accountFixture(page)
  for (const mode of ['light', 'dark']) {
    await page.emulateMedia({ colorScheme: mode })
    await expect(page.locator('html')).toHaveAttribute('data-theme', mode)
    const result = await page.locator('.account-panel .status-pill.verified').evaluate(el => {
      const style = getComputedStyle(el)
      const luma = color => color.match(/[\d.]+/g).slice(0, 3).map(Number).map(c => c / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4).reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0)
      const a = luma(style.color), b = luma(style.backgroundColor)
      return { contrast: (Math.max(a, b) + .05) / (Math.min(a, b) + .05), backgroundLuminance: b }
    })
    expect(result.contrast).toBeGreaterThanOrEqual(4.5)
    if (mode === 'dark') expect(result.backgroundLuminance).toBeLessThan(.1)
  }
})

test('signout dialog supports cancel, close, Escape and trapped keyboard focus without ending the session', async ({ page }) => {
  const requests = await accountFixture(page)
  const opener = page.getByRole('button', { name: 'Đăng xuất', exact: true })
  await opener.click()
  const dialog = page.getByRole('dialog', { name: 'Đăng xuất khỏi tài khoản?' })
  await expect(dialog.getByRole('button', { name: 'Ở lại' })).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(dialog.getByRole('button', { name: 'Đăng xuất', exact: true })).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(dialog.getByRole('button', { name: 'Đóng hộp xác nhận' })).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(dialog.getByRole('button', { name: 'Đăng xuất', exact: true })).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(dialog).not.toBeVisible()
  await expect(opener).toBeFocused()
  await opener.click()
  await dialog.getByRole('button', { name: 'Đóng hộp xác nhận' }).click()
  await expect(dialog).not.toBeVisible()
  for (const width of [1440, 768, 375, 320]) {
    await page.setViewportSize({ width, height: 800 })
    if (width <= 900) await page.getByRole('button', { name: 'Mở điều hướng', exact: true }).click()
    await opener.click()
    await expect(dialog).toBeVisible()
    const size = await dialog.boundingBox()
    expect(size.x).toBeGreaterThanOrEqual(0)
    expect(size.x + size.width).toBeLessThanOrEqual(width + 1)
    await dialog.getByRole('button', { name: 'Ở lại' }).click()
    await expect(dialog).not.toBeVisible()
    if (width <= 900) await page.getByRole('button', { name: 'Đóng điều hướng', exact: true }).click()
  }
  expect(requests).toEqual([])
})

test('confirming signout ends only the requested session and returns to login', async ({ page }) => {
  const requests = await accountFixture(page)
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại' })).toBeVisible()
  expect(requests).toEqual(['POST'])
})
