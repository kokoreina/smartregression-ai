// A slow response may not display the previous commit's impact under a new SHA.
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'
const origin = 'https://localhost:8444'
const root = fileURLToPath(new URL('../../var/phase3-8/request-identity/', import.meta.url))
await fs.mkdir(root, { recursive: true })
const browser = await chromium.launch({ executablePath: process.env.SMARTREGRESSION_TEST_CHROMIUM, headless: true })
const context = await browser.newContext({ ignoreHTTPSErrors: true })
const page = await context.newPage()
async function post(path, data) {
  const csrf = await (await context.request.get(origin + '/api/v1/auth/csrf')).json()
  return context.request.post(origin + '/api/v1' + path, { data, headers: { Origin: origin, 'X-CSRF-Token': csrf.token } })
}
let release
try {
  const email = `identity_${Date.now()}@example.com`
  const password = 'Synthetic request identity password 2026!'
  assert.equal((await post('/auth/register', { email, password, display_name: 'Request identity fixture' })).status(), 202)
  const inbox = await (await context.request.get(`${origin}/__test__/mail?email=${encodeURIComponent(email)}`, { headers: { 'X-Test-Inbox': 'synthetic-e2e-only' } })).json()
  await page.goto(inbox.messages.at(-1).body.trim())
  await page.getByRole('button', { name: 'Xác nhận email', exact: true }).click()
  await page.getByText('Email đã được xác thực.', { exact: false }).waitFor()
  assert.equal((await post('/auth/login', { email, password })).status(), 200)
  const project = await (await post('/projects', { title: 'Synthetic request identity', repository_url: 'https://github.com/owner/repo' })).json()
  const base = 'a'.repeat(40); const target = 'b'.repeat(40)
  for (const commit of [base, target]) assert.equal((await post(`/projects/${project.id}/snapshots`, { commit })).status(), 200)
  assert.equal((await post(`/projects/${project.id}/notes`, { commit: base, path: 'app.py', title: 'Baseline anchor', kind: 'pin' })).status(), 201)
  await page.goto(`${origin}/app/projects/${project.id}/explorer?commit=${target}&path=app.py`)
  await page.getByRole('heading', { name: 'Ảnh hưởng tiềm năng theo phân tích tĩnh', exact: true }).waitFor()
  const gate = new Promise(resolve => { release = resolve })
  await page.route(`**/snapshots/${base}/impact?*`, async route => { const response = await route.fetch(); await gate; await route.fulfill({ response }) })
  await page.getByText('Ghi chú và ghim', { exact: false }).click()
  await page.getByRole('link', { name: 'app.py · aaaaaaaa', exact: true }).click()
  await page.getByText('Commit: aaaaaaaaaaaa', { exact: true }).waitFor()
  await page.getByRole('heading', { name: 'Quan hệ tĩnh', exact: true }).waitFor()
  assert.equal(await page.getByRole('heading', { name: 'Ảnh hưởng tiềm năng theo phân tích tĩnh', exact: true }).count(), 0, 'Previous target impact must be hidden while base impact is pending')
  release()
  await page.getByRole('heading', { name: 'Ảnh hưởng tiềm năng theo phân tích tĩnh', exact: true }).waitFor()
  await fs.writeFile(root + 'result.json', JSON.stringify({ passed: true, scope: 'real PostgreSQL/snapshots; only transport timing delayed in browser; no provider', stale_impact_hidden_until_matching_commit_response: true }, null, 2))
  console.log(JSON.stringify({ passed: true, artifact: root + 'result.json' }))
} finally { release?.(); await browser.close() }
