import { test, expect } from '@playwright/test'
import { fileURLToPath } from 'node:url'

async function offlineReports(page) {
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname
    return path.endsWith('/capabilities') ? route.fulfill({ json: { local_demo: false } }) : route.fulfill({ status: 401, json: { code: 'authentication_required' } })
  })
  await page.goto('/reports')
  await expect(page.getByRole('heading', { level: 1, name: 'Báo cáo đã lưu' })).toBeVisible()
}

async function choose(page, name) {
  const mode = name === 'Tối' ? 'dark' : 'light'
  if (await page.locator('html').getAttribute('data-theme') !== mode) await page.getByRole('button', { name: `Chuyển sang giao diện ${mode === 'dark' ? 'tối' : 'sáng'}`, exact: true }).click()
}

test('system theme follows the OS while an explicit choice persists across reloads', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' })
  await offlineReports(page)
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await expect(page.locator('html')).toHaveAttribute('data-theme-preference', 'system')
  await page.emulateMedia({ colorScheme: 'light' })
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  await page.emulateMedia({ colorScheme: 'dark' })
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await choose(page, 'Sáng')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  expect(await page.evaluate(() => localStorage.getItem('smartregression.theme'))).toBe('light')
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  await page.emulateMedia({ colorScheme: 'light' })
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  await choose(page, 'Tối')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
})

test('one keyboard activation changes the theme without opening a menu', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' })
  await offlineReports(page)
  const toggle = page.locator('.theme-toggle')
  await toggle.focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await expect(toggle).toBeFocused()
  await expect(page.locator('.theme-options')).toHaveCount(0)
  await page.keyboard.press('Space')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
})

test('theme choice synchronizes between tabs', async ({ page, context }) => {
  await offlineReports(page)
  const other = await context.newPage()
  await offlineReports(other)
  await choose(page, 'Tối')
  await expect(other.locator('html')).toHaveAttribute('data-theme', 'dark')
  await choose(other, 'Sáng')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
})

test('blocked browser storage still allows a theme choice in the current tab', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' })
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => { throw new DOMException('Disabled', 'SecurityError') }
    Storage.prototype.setItem = () => { throw new DOMException('Disabled', 'SecurityError') }
  })
  await offlineReports(page)
  await choose(page, 'Tối')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await page.getByRole('link', { name: 'Đăng nhập', exact: true }).click()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await expect(page.getByRole('heading', { level: 1, name: 'Chào mừng trở lại' })).toBeVisible()
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
})

test('invalid stored theme falls back to the system before React mounts', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' })
  await page.addInitScript(() => localStorage.setItem('smartregression.theme', 'invalid'))
  await page.route('**/src/app/main.tsx', route => route.abort())
  await page.goto('/reports')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await expect(page.locator('html')).toHaveAttribute('data-theme-preference', 'system')
  await expect(page.locator('html')).toHaveCSS('color-scheme', 'dark')
})

test('login and keyboard skip link keep the saved dark palette', async ({ page }) => {
  await offlineReports(page)
  await choose(page, 'Tối')
  await page.getByRole('link', { name: 'Đăng nhập', exact: true }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Chào mừng trở lại' })).toBeVisible()
  await expect(page.locator('.auth-main .auth-card')).toHaveCSS('background-color', 'rgb(24, 31, 43)')
  await expect(page.locator('.auth-main .eyebrow')).toHaveCSS('color', 'rgb(167, 179, 196)')
  await page.getByRole('link', { name: 'Bỏ qua đến nội dung' }).focus()
  await expect(page.locator('.skip-link')).toHaveCSS('background-color', 'rgb(35, 45, 61)')
  await expect(page.locator('.skip-link')).toHaveCSS('color', 'rgb(233, 238, 245)')
})

test('dark reports remain readable at six widths, and print uses a light surface', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' })
  await offlineReports(page)
  for (const width of [1920, 1440, 1280, 1024, 768, 375]) {
    await page.setViewportSize({ width, height: 1000 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `dark report overflow at ${width}px`).toBe(true)
    await page.screenshot({ path: `../var/uiux-playwright/reports-dark-${width}.png`, fullPage: true })
  }
  await page.setViewportSize({ width: 1440, height: 1000 })
  await expect(page.locator('.report-import-main')).toHaveCSS('background-color', 'rgb(19, 26, 36)')
  await expect(page.getByRole('button', { name: 'Chọn file JSON', exact: true })).toHaveCSS('color', 'rgb(16, 44, 37)')
  await page.getByLabel('Chọn báo cáo JSON').setInputFiles(fileURLToPath(new URL('../../examples/reports/stage-report.partial.json', import.meta.url)))
  await expect(page.locator('.saved-report-content .card').first()).toHaveCSS('background-color', 'rgb(24, 31, 43)')
  await expect(page.locator('.status-completed').first()).toHaveCSS('color', 'rgb(158, 217, 180)')
  await page.screenshot({ path: '../var/uiux-playwright/report-open-dark.png', fullPage: true })
  await page.emulateMedia({ media: 'print' })
  await expect(page.locator('.saved-report-content .card').first()).toHaveCSS('background-color', 'rgb(255, 255, 255)')
  await expect(page.locator('.theme-switcher')).not.toBeVisible()
})

test('primary, secondary and status text meets AA contrast in both themes', async ({ page }) => {
  await offlineReports(page)
  async function contrast(selector) {
    return page.locator(selector).first().evaluate(element => {
      const rgba = value => {
        const parts = value.match(/[\d.]+/g).map(Number)
        if (value.startsWith('color(srgb')) return [...parts.slice(0, 3).map(v => v * 255), parts[3] ?? 1]
        return [...parts.slice(0, 3), parts[3] ?? 1]
      }
      const blend = (front, back) => front.slice(0, 3).map((v, i) => v * front[3] + back[i] * (1 - front[3]))
      const parents = []
      for (let node = element; node; node = node.parentElement) parents.unshift(node)
      let background = [255, 255, 255]
      for (const parent of parents) background = blend(rgba(getComputedStyle(parent).backgroundColor), background)
      const foreground = blend(rgba(getComputedStyle(element).color), background)
      const luminance = rgb => rgb.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0)
      const a = luminance(foreground), b = luminance(background)
      return (Math.max(a, b) + .05) / (Math.min(a, b) + .05)
    })
  }
  for (const name of ['Sáng', 'Tối']) {
    await choose(page, name)
    for (const selector of ['h1', '.report-import-main p', '.report-import-main button', '.report-format-guide dd', '.workspace-sidebar nav a.active', '.workspace-header .status-pill']) expect(await contrast(selector), `${name}: ${selector}`).toBeGreaterThanOrEqual(4.5)
  }
  await page.getByLabel('Chọn báo cáo JSON').setInputFiles(fileURLToPath(new URL('../../examples/reports/stage-report.partial.json', import.meta.url)))
  for (const name of ['Sáng', 'Tối']) {
    await choose(page, name)
    for (const selector of ['.status-completed', '.status-partial', '.status-not-implemented', '.badge', '.saved-report-content .muted']) expect(await contrast(selector), `${name}: ${selector}`).toBeGreaterThanOrEqual(4.5)
  }
})
