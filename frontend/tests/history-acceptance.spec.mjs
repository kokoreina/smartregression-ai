import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'

const project = '11111111-1111-4111-8111-111111111111'
const first = '22222222-2222-4222-8222-222222222222'
const second = '33333333-3333-4333-8333-333333333333'
const base = 'a'.repeat(40), target = 'b'.repeat(40)
const projectURL = `/app/projects/${project}?section=runs`

async function fixture(page, { archived = false, denied = false } = {}) {
  const requests = []
  const stage = JSON.parse(await readFile(new URL('../../examples/reports/stage-report.partial.json', import.meta.url), 'utf8'))
  const run = (id, status = 'failed') => ({ schema_version: '1.0.0', id, project_id: project,
    repository_url: 'https://github.com/owner/repo', base, target, config_digest: 'c'.repeat(64),
    status, started_at: '2026-11-01T00:00:00Z', finished_at: '2026-11-01T00:01:00Z',
    error_code: status === 'failed' ? 'synthetic_fixture' : null, report_available: status === 'completed', ai_status: 'not_run' })
  await page.route('**/api/v1/**', route => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname
    requests.push({ path, method: request.method(), status: url.searchParams.get('status'), cursor: url.searchParams.get('cursor') })
    if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
    if (path.endsWith('/auth/me')) return route.fulfill({ json: { schema_version: '1.0.0', id: project, email: 'fixture@example.com', display_name: 'History fixture · DEMO', verified: true } })
    if (path === `/api/v1/projects/${project}`) return route.fulfill({ json: { id: project, title: 'History · DEMO', description: '', repository_url: 'https://github.com/owner/repo', archived, version: 1, created_at: '2026-11-01T00:00:00Z', updated_at: '2026-11-01T00:00:00Z' } })
    if (path.endsWith('/view-state')) return route.fulfill({ json: null })
    if (path.endsWith('/runs')) {
      const filtered = url.searchParams.get('status') === 'failed'
      const more = url.searchParams.has('cursor')
      return route.fulfill({ json: { items: more ? [run(second)] : filtered ? [run(first)] : [run(first), run(second, 'completed')], next_cursor: filtered && !more ? 'fixture-cursor' : null } })
    }
    if (path.endsWith(`/runs/${second}`)) return route.fulfill(denied ? { status: 404, json: { code: 'run_not_found' } } : { json: run(second, 'completed') })
    if (path.endsWith(`/runs/${second}/report`)) return route.fulfill({ json: {
      schema_version: '1.0.0', run: run(second, 'completed'), payload: { schema_version: '1.0.0',
        repository: { schema_version: '1.0.0', repository_url: 'https://github.com/owner/repo', full_name: 'owner/repo', default_branch: 'main', commits: [] },
        files: [], report: stage, narrative: { status: 'not_run' }, narrative_evidence: [], selection_status: 'not_run', execution_status: 'not_run', limitations: ['Fixture · DEMO'] } } })
    if (path.endsWith('/usage')) return route.fulfill({ json: { granted_calls: 0, used_calls: 0, cap_micro_usd: 0, reserved_micro_usd: 0, known_actual_micro_usd: 0, unknown_actual_count: 0 } })
    return route.fulfill({ status: 404, json: { code: 'not_found' } })
  })
  return requests
}

test('history status filter is server-side, survives reload and paginates without stale rows', async ({ page }) => {
  const requests = await fixture(page)
  await page.goto(projectURL)
  await expect(page.getByRole('link', { name: 'Đã kết thúc phân tích', exact: true })).toBeVisible()
  await page.getByLabel('Lọc trạng thái lịch sử').selectOption('failed')
  await expect(page).toHaveURL(/runStatus=failed/)
  await expect(page.getByRole('link', { name: 'Đã kết thúc phân tích', exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Tải thêm lịch sử', exact: true }).click()
  await expect(page.getByRole('link', { name: 'Phân tích lỗi', exact: true })).toHaveCount(2)
  expect(requests.some(r => r.cursor === 'fixture-cursor' && r.status === 'failed')).toBe(true)
  await page.reload()
  await expect(page.getByLabel('Lọc trạng thái lịch sử')).toHaveValue('failed')
  await expect(page.getByRole('link', { name: 'Phân tích lỗi', exact: true })).toHaveCount(1)
  expect(requests.every(r => r.method === 'GET')).toBe(true)
})

test('reopening and reloading a saved partial report never creates run or AI jobs', async ({ page }) => {
  const requests = await fixture(page)
  await page.goto(`/app/projects/${project}/runs/${second}`)
  await expect(page.getByRole('heading', { name: 'Chi tiết phân tích', exact: true })).toBeVisible()
  await expect(page.getByText(`${base} → ${target}`, { exact: true })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Kết quả: owner/repo', exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('region', { name: 'Kết quả: owner/repo', exact: true })).toBeVisible()
  expect(requests.filter(r => r.path.endsWith('/report')).length).toBeGreaterThanOrEqual(2)
  expect(requests.every(r => r.method === 'GET')).toBe(true)
  expect(requests.some(r => r.path.includes('/ai'))).toBe(false)
})

test('archived project keeps history readable without offering a new analysis', async ({ page }) => {
  const requests = await fixture(page, { archived: true })
  await page.goto(projectURL)
  await expect(page.getByText('Dự án đã lưu trữ: bạn vẫn có thể mở báo cáo cũ.', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Phân tích tĩnh và lưu kết quả', exact: true })).toHaveCount(0)
  await page.getByRole('link', { name: 'Đã kết thúc phân tích', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Kết quả: owner/repo', exact: true })).toBeVisible()
  expect(requests.every(r => r.method === 'GET')).toBe(true)
})

test('foreign or missing run never reveals a report', async ({ page }) => {
  const requests = await fixture(page, { denied: true })
  await page.goto(`/app/projects/${project}/runs/${second}`)
  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Kết quả: owner/repo', exact: true })).toHaveCount(0)
  expect(requests.some(r => r.path.endsWith('/report'))).toBe(false)
})

test('revoked session redirects on reload before reading saved run again', async ({ page }) => {
  const requests = await fixture(page)
  await page.goto(`/app/projects/${project}/runs/${second}`)
  await expect(page.getByRole('region', { name: 'Kết quả: owner/repo', exact: true })).toBeVisible()
  const before = requests.filter(r => r.path.includes('/runs/')).length
  await page.route('**/api/v1/auth/me', route => route.fulfill({ status: 401, json: { code: 'authentication_required' } }))
  await page.reload()
  await expect(page).toHaveURL(/\/login/)
  expect(requests.filter(r => r.path.includes('/runs/')).length).toBe(before)
})
