import { test, expect } from '@playwright/test'

const project = '11111111-1111-4111-8111-111111111111'
const thread = '22222222-2222-4222-8222-222222222222'
const commit = 'a'.repeat(40)
const old = 'b'.repeat(40)
const root = `/projects/${project}/assistant`
const pageUrl = `/app/projects/${project}?section=assistant`
const date = '2026-11-19T00:00:00Z'
const proof = { id: 'proof-1', commit, path: 'app.py', kind: 'source_range', line_start: 1, line_end: 2, source_kind: 'git', overlay_digest: null }
const coverage = { status: 'partial', analyzed_files: ['app.py', 'billing.py'], unsupported_files: ['README.md'], unparsed_files: [] }
const reply = { schema_version: '1.0.0', commit, kind: 'overview', summary: 'DEMO: Hai file Python và tài liệu dự án được đối chiếu theo commit.', facts: [{ text: 'DEMO: app.py import billing.py.', evidence: [proof] }], coverage, limitations: ['Quan hệ tĩnh chưa chứng minh hành vi khi chạy.'], excerpts: [{ commit, path: 'app.py', line_start: 1, line_end: 2, content: 'import billing\nbilling.invoice()' }] }

async function fixture(page, options = {}) {
  const calls = { messages: [], previews: [], watches: [], threads: [], checks: 0 }
  let threads = []
  let messages = []
  let watch = null
  const notification = { schema_version: '1.0.0', id: '33333333-3333-4333-8333-333333333333', created_at: date, read_at: null, report: { schema_version: '1.0.0', base: old, target: commit, config_digest: 'c'.repeat(64), branch: 'main', changes: [{ path: 'billing.py', change: 'modified' }], scope: ['app.py'], scope_impacts: [{ path: 'app.py', relationship: 'direct', chain: ['billing.py', 'app.py'], evidence: [proof] }], impacts_truncated: false, base_coverage: coverage, target_coverage: coverage, limitations: ['Chưa tìm thấy liên hệ không đồng nghĩa không ảnh hưởng.'] } }
  await page.route('**/api/v1/**', async route => {
    const request = route.request()
    const path = new URL(request.url()).pathname.replace('/api/v1', '')
    const respond = (json, status = 200) => route.fulfill({ status, json })
    if (path === '/capabilities') return respond({ local_demo: false })
    if (path === '/auth/me') return respond({ id: project, email: 'fixture@example.com', display_name: 'Kiểm thử · DEMO', verified: true })
    if (path === '/auth/csrf') return respond({ token: 'synthetic-only-csrf' })
    if (path === `/projects/${project}`) return respond({ id: project, title: 'Trợ lý repository · DEMO', repository_url: 'https://github.com/example/fixture', description: 'Synthetic browser fixture', archived: false, version: 1, created_at: date, updated_at: date })
    if (path.endsWith('/repository')) return respond({ repository_url: 'https://github.com/example/fixture', full_name: 'example/fixture', default_branch: 'main', commits: [{ sha: commit, message: 'DEMO', date }] })
    if (path === `${root}/overview`) return options.overviewError ? respond({ code: 'github_rate_limit' }, 422) : respond(reply)
    if (path === `${root}/threads`) {
      if (request.method() === 'POST') { const body = request.postDataJSON(); calls.threads.push(body); const value = { id: `22222222-2222-4222-8222-${String(threads.length + 1).padStart(12, '0')}`, project_id: project, commit: body.commit, config_digest: 'c'.repeat(64), title: body.title, created_at: date }; threads = [value, ...threads]; return respond(value) }
      return respond(threads)
    }
    if (path.endsWith('/preview')) { calls.previews.push(request.postDataJSON()); return respond(reply) }
    if (path.endsWith('/messages')) {
      if (request.method() === 'POST') {
        const body = request.postDataJSON(); calls.messages.push(body)
        if (options.quota && body.use_llm) return respond({ code: 'ai_quota_exhausted' }, 409)
        const ai = body.use_llm ? { id: thread, run_id: null, scope_key: `${commit}:thread:${thread}`, context_hash: 'c'.repeat(64), provenance: { observations: [proof] }, status: 'completed', action: body.action, created_at: date, finished_at: date, result: { status: 'completed', model: 'gemini-3.8-flash', data: { summary: 'DEMO: Gemini giải thích quan hệ import đã cung cấp.', findings: [{ path: 'app.py', explanation: 'DEMO: cần xem hợp đồng invoice.', evidence_ids: [proof.id] }], limitations: ['Chưa chạy test.'] } } } : null
        if (ai && options.unavailable) { ai.status = 'failed'; ai.result = { status: 'failed', error_code: 'provider_unavailable' }; ai.provenance = { observations: [proof], requested_model: 'gemini-3.8-flash', attempt: 3 } }
        if (ai && options.fallback && body.allow_model_fallback) { ai.result.model = 'gemini-3.5-flash-lite'; ai.provenance = { observations: [proof], requested_model: 'gemini-3.5-flash-lite', attempt: 3 } }
        const value = { id: `44444444-4444-4444-8444-${String(messages.length).padStart(12, '0')}`, thread_id: path.split('/threads/')[1].split('/')[0], question: body.question, reply: { ...reply, kind: body.action === 'overview' ? 'overview' : body.action === 'changes' ? 'changes' : 'search' }, ai, created_at: date }
        messages.push(value); return respond(value)
      }
      return respond(messages.filter(value => value.thread_id === path.split('/threads/')[1].split('/')[0]))
    }
    if (path === `${root}/watch`) {
      if (request.method() === 'PUT') { const body = request.postDataJSON(); calls.watches.push(body); watch = { ...body, version: body.version + 1, last_commit: commit, checked_at: date, next_check_at: date, pending: false, error_code: null } }
      return respond(watch)
    }
    if (path === `${root}/check`) { calls.checks++; return respond({ ...watch, pending: true }, 202) }
    if (path === `${root}/notifications`) return respond(options.notifications ? [notification] : [])
    if (path.endsWith('/read')) { notification.read_at = date; return route.fulfill({ status: 204 }) }
    return respond({ code: 'fixture_route_not_found' }, 404)
  })
  return calls
}

test('onboarding shows static overview without an AI call and allows grounded questions', async ({ page }) => {
  const calls = await fixture(page)
  await page.goto(pageUrl)
  await expect(page.getByRole('heading', { name: 'Hiểu mã nguồn, theo sát thay đổi' })).toBeVisible()
  await expect(page.locator('.assistant-overview')).toContainText('DEMO: Hai file Python')
  expect(calls.messages).toHaveLength(0)
  await page.getByLabel('Câu hỏi về dự án', { exact: true }).fill('invoice được gọi ở đâu?')
  await page.getByRole('button', { name: 'Tìm bằng chứng', exact: true }).click()
  await expect(page.locator('.assistant-message')).toHaveCount(1)
  expect(calls.messages[0].use_llm).toBe(false)
  expect(calls.messages[0].excerpts).toEqual([])
  await page.locator('.assistant-message .assistant-facts summary').click()
  await expect(page.locator('.assistant-message .assistant-citation').first()).toHaveAttribute('href', new RegExp(`commit=${commit}.*path=app.py`))
})

test('AI source egress requires a question-specific preview and separate consent', async ({ page }) => {
  const calls = await fixture(page)
  await page.goto(pageUrl)
  await page.getByLabel('Câu hỏi về dự án', { exact: true }).fill('invoice')
  await page.getByRole('checkbox', { name: /Dùng Gemini 3.8 Flash/ }).check()
  await expect(page.locator('.assistant-egress')).toHaveCount(0)
  await page.getByRole('button', { name: 'Xem bằng chứng trước khi hỏi AI' }).click()
  await page.locator('.assistant-egress summary').click()
  await expect(page.locator('.assistant-egress pre')).toContainText('import billing')
  await page.getByRole('checkbox', { name: 'Tôi đồng ý gửi đúng các trích đoạn đang hiển thị.' }).check()
  await page.getByRole('button', { name: 'Hỏi Gemini', exact: true }).click()
  await expect(page.locator('.assistant-generated')).toContainText('gemini-3.8-flash')
  expect(calls.previews).toHaveLength(1)
  expect(calls.messages[0].allow_excerpt_egress).toBe(true)
  expect(calls.messages[0].excerpts).toEqual([{ path: 'app.py', start: 1, end: 2 }])
  await page.getByLabel('Câu hỏi về dự án', { exact: true }).fill('câu hỏi mới')
  await expect(page.locator('.assistant-egress')).toHaveCount(0)
})

test('watch saves explicit scope and manual check reports completion without a fake alert', async ({ page }) => {
  const calls = await fixture(page)
  await page.goto(pageUrl)
  await expect(page.getByLabel('Nhánh GitHub')).toHaveValue('main')
  await page.getByLabel('File hoặc thư mục · mỗi dòng một đường dẫn').fill('app.py\nsrc')
  await page.getByRole('button', { name: 'Lưu theo dõi', exact: true }).click()
  await expect(page.locator('.assistant-sync-status')).toBeVisible()
  expect(calls.watches[0].paths).toEqual(['app.py', 'src'])
  await page.getByRole('button', { name: 'Kiểm tra thay đổi mới', exact: true }).click()
  await expect(page.getByRole('status').filter({ hasText: 'Đã đồng bộ nhánh' })).toBeVisible()
  expect(calls.checks).toBe(1)
  await expect(page.locator('.assistant-notification')).toHaveCount(0)
})

test('change evidence shows dependency path and read action accepts a genuine 204', async ({ page }) => {
  await fixture(page, { notifications: true })
  await page.goto(pageUrl)
  const notification = page.locator('.assistant-notification')
  await expect(page.locator('.assistant-notifications')).toContainText('1 chưa đọc')
  await notification.getByText('Xem thay đổi và đường ảnh hưởng', { exact: true }).click()
  await expect(notification.getByRole('list', { name: 'Đường ảnh hưởng tới app.py' })).toContainText('billing.py')
  await expect(notification).toContainText('không đồng nghĩa không ảnh hưởng')
  await notification.getByRole('button', { name: 'Đánh dấu đã đọc' }).click()
  await expect(notification).toHaveClass(/is-read/)
  await expect(page.locator('.assistant-notifications')).toContainText('0 chưa đọc')
})

test('quota failure retains the question and static overview', async ({ page }) => {
  await fixture(page, { quota: true })
  await page.goto(pageUrl)
  await page.getByLabel('Câu hỏi về dự án', { exact: true }).fill('invoice')
  await page.getByRole('checkbox', { name: /Dùng Gemini 3.8 Flash/ }).check()
  await page.getByRole('button', { name: 'Hỏi Gemini', exact: true }).click()
  await expect(page.locator('.form-notice.is-error')).toContainText('quota')
  await expect(page.getByLabel('Câu hỏi về dự án', { exact: true })).toHaveValue('invoice')
  await expect(page.locator('.assistant-overview')).toBeVisible()
})

test('503 explains temporary overload and drafting again does not make another API request', async ({ page }) => {
  const calls = await fixture(page, { unavailable: true })
  await page.goto(pageUrl)
  await page.getByLabel('Câu hỏi về dự án', { exact: true }).fill('invoice')
  await page.getByRole('checkbox', { name: /Dùng Gemini 3.8 Flash/ }).check()
  await page.getByRole('button', { name: 'Hỏi Gemini', exact: true }).click()
  await expect(page.locator('.assistant-provider-unavailable')).toContainText('Gemini đang tạm quá tải (503)')
  await expect(page.locator('.assistant-generated')).toContainText('Lượt 3/3')
  await page.getByRole('button', { name: 'Soạn câu hỏi lại' }).click()
  await expect(page.getByLabel('Câu hỏi về dự án', { exact: true })).toHaveValue('invoice')
  expect(calls.messages).toHaveLength(1)
  expect(calls.messages[0].allow_model_fallback).toBe(false)
})

test('fallback requires opt-in and discloses the model that answered', async ({ page }) => {
  const calls = await fixture(page, { fallback: true })
  await page.goto(pageUrl)
  await page.getByLabel('Câu hỏi về dự án', { exact: true }).fill('invoice')
  await page.getByRole('checkbox', { name: /Dùng Gemini 3.8 Flash/ }).check()
  const fallback = page.getByRole('checkbox', { name: /Cho phép dùng Gemini 3.5 Flash-Lite/ })
  await expect(fallback).not.toBeChecked()
  await fallback.check()
  await page.getByRole('button', { name: 'Hỏi Gemini', exact: true }).click()
  await expect(page.locator('.assistant-generated h4')).toContainText('gemini-3.5-flash-lite')
  await expect(page.locator('.assistant-generated')).toContainText('đã chọn model dự phòng')
  expect(calls.messages[0].allow_model_fallback).toBe(true)
})

test('new conversation and switching history preserve separate messages', async ({ page }) => {
  const calls = await fixture(page)
  await page.goto(pageUrl)
  await page.getByRole('button', { name: 'Giải thích tổng quan', exact: true }).click()
  await expect(page.getByRole('combobox', { name: 'Phạm vi', exact: true })).toHaveValue('overview')
  await page.getByRole('button', { name: 'Tìm bằng chứng', exact: true }).click()
  await expect(page.locator('.assistant-message')).toHaveCount(1)
  const first = await page.getByLabel('Hội thoại đã lưu').inputValue()
  await page.getByRole('button', { name: 'Hội thoại mới', exact: true }).click()
  await expect(page.locator('.assistant-message')).toHaveCount(0)
  await expect(page.getByLabel('Hội thoại đã lưu')).not.toHaveValue(first)
  await page.getByLabel('Hội thoại đã lưu').selectOption(first)
  await expect(page.locator('.assistant-message')).toHaveCount(1)
  await page.locator('.assistant-message .assistant-limits > summary').click()
  await expect(page.locator('.assistant-message')).toContainText('Phạm vi phân tích của snapshot')
  expect(calls.messages).toHaveLength(1)
})

test('automatic watch saves interval and optimistic version', async ({ page }) => {
  const calls = await fixture(page)
  await page.goto(pageUrl)
  await expect(page.getByLabel('Nhánh GitHub')).toHaveValue('main')
  await page.getByRole('checkbox', { name: 'Tự kiểm tra khi worker đang chạy' }).check()
  await page.getByLabel('Chu kỳ kiểm tra').selectOption('1800')
  await page.getByRole('button', { name: 'Lưu theo dõi', exact: true }).click()
  await expect(page.locator('.assistant-sync-status')).toBeVisible()
  await page.getByLabel('File hoặc thư mục · mỗi dòng một đường dẫn').fill('app.py')
  await page.getByRole('button', { name: 'Lưu theo dõi', exact: true }).click()
  await expect.poll(() => calls.watches.length).toBe(2)
  expect(calls.watches[0]).toMatchObject({ automatic: true, interval_seconds: 1800, version: 0 })
  expect(calls.watches[1]).toMatchObject({ automatic: true, interval_seconds: 1800, version: 1 })
})

test('asking about a notification pins its target and uses the change action', async ({ page }) => {
  const calls = await fixture(page, { notifications: true })
  await page.goto(pageUrl)
  await page.getByRole('button', { name: 'Hỏi về thay đổi', exact: true }).click()
  await expect(page.getByRole('combobox', { name: 'Phạm vi', exact: true })).toHaveValue('changes')
  await page.getByRole('button', { name: 'Tìm bằng chứng', exact: true }).click()
  await expect(page.locator('.assistant-message')).toHaveCount(1)
  expect(calls.threads[0].commit).toBe(commit)
  expect(calls.messages[0].action).toBe('changes')
})

for (const theme of ['light', 'dark']) {
  test(`assistant ${theme} layout remains readable from desktop to mobile`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: theme, reducedMotion: 'reduce' })
    await fixture(page, { notifications: true })
    await page.goto(pageUrl)
    await expect(page.locator('.assistant-heading')).toHaveCSS('background-color', 'rgba(0, 0, 0, 0)')
    await expect(page.locator('.assistant-heading h2')).toHaveCSS('color', theme === 'dark' ? 'rgb(233, 238, 245)' : 'rgb(31, 41, 51)')
    await page.locator('.assistant-excerpts summary').click()
    await expect(page.locator('.assistant-excerpts pre')).toHaveCSS('background-color', theme === 'dark' ? 'rgb(19, 26, 36)' : 'rgb(247, 249, 250)')
    for (const width of [1440, 1024, 768, 375, 320]) {
      await page.setViewportSize({ width, height: 1000 })
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `overflow at ${width}`).toBe(true)
      if ([1440, 375].includes(width)) await page.screenshot({ path: `../var/uiux-playwright/assistant-${theme}-${width}.png`, fullPage: true })
    }
    await page.getByLabel('Câu hỏi về dự án', { exact: true }).focus()
    await expect(page.getByLabel('Câu hỏi về dự án', { exact: true })).toBeFocused()
  })
}
