import { test, expect } from '@playwright/test'

const project = '11111111-1111-4111-8111-111111111111'
const a = '22222222-2222-4222-8222-222222222222', b = '33333333-3333-4333-8333-333333333333'
const sha = 'a'.repeat(40)

test('failed comparison in another mode cannot leave a previous success on screen', async ({ page }) => {
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
    if (path.endsWith('/auth/me')) return route.fulfill({ json: { id: project, email: 'fixture@example.com', display_name: 'Comparison · DEMO', verified: true } })
    if (path.endsWith('/auth/csrf')) return route.fulfill({ json: { token: 'synthetic-csrf' } })
    if (path.endsWith('/scenarios')) return route.fulfill({ json: { items: [a, b].map((id, i) => ({ id, project_id: project, baseline: sha, title: `Option ${i + 1}`, analysis_kind: 'hypothesis', mode: 'description', impact: null, limitations: [] })), next_cursor: null } })
    if (path.endsWith('/scenario-comparisons')) return route.fulfill({ json: { left: a, right: b, baseline: sha, config_digest: 'c'.repeat(64), comparison_kind: 'static_overlay', added_affected: [], removed_affected: [], retained_affected: [], graph_delta: { base_commit: sha, target_commit: sha, total_added_nodes: 0, total_removed_nodes: 1, retained_node_count: 0, total_added_edges: 0, total_removed_edges: 0, retained_edge_count: 0, added_nodes: [], removed_nodes: [{ id: 'overlay-old', path: 'option_a.py', kind: 'file', evidence: { source_kind: 'overlay', overlay_digest: 'd'.repeat(64) } }], limitations: [] }, unresolved_left: 0, unresolved_right: 0, interpretation: 'no_safety_ranking' } })
    if (path.endsWith('/graph') && path.includes('/scenarios/')) return route.fulfill({ json: { commit: sha, nodes: [], edges: [], total_nodes: 0, total_edges: 0, truncated: false } })
    if (path.endsWith('/graph-comparisons')) return route.fulfill({ status: 409, json: { code: 'scenario_baseline_mismatch' } })
    return route.fulfill({ status: 404, json: { code: 'not_found' } })
  })
  await page.goto(`/app/projects/${project}/what-if`)
  await page.getByLabel('Phương án A', { exact: true }).selectOption(a)
  await page.getByLabel('Phương án B', { exact: true }).selectOption(b)
  await page.getByRole('button', { name: 'So sánh hai phương án', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Kết quả A/B đã tính', exact: true })).toBeVisible()
  await expect(page.getByText('option_a.py · overlay phương án A', { exact: true })).toBeVisible()
  await page.getByLabel('Base commit', { exact: true }).fill(sha)
  await page.getByLabel('Target commit', { exact: true }).fill('b'.repeat(40))
  await page.getByRole('button', { name: 'So sánh graph phiên bản', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Kết quả A/B đã tính', exact: true })).toHaveCount(0)
  await expect(page.locator('.comparison-graphs')).toHaveCount(0)
})

for (const graphFailure of [false, true]) {
  test(`version comparison publishes a complete result only after both graphs load: failure=${graphFailure}`, async ({ page }) => {
    const target = 'b'.repeat(40)
    await page.route('**/api/v1/**', route => {
      const path = new URL(route.request().url()).pathname
      if (path.endsWith('/capabilities')) return route.fulfill({ json: { local_demo: false } })
      if (path.endsWith('/auth/me')) return route.fulfill({ json: { id: project, email: 'fixture@example.com', display_name: 'Comparison · DEMO', verified: true } })
      if (path.endsWith('/auth/csrf')) return route.fulfill({ json: { token: 'synthetic-csrf' } })
      if (path.endsWith('/scenarios')) return route.fulfill({ json: { items: [], next_cursor: null } })
      if (path.endsWith('/graph-comparisons')) return route.fulfill({ json: { base_commit: sha, target_commit: target, total_added_nodes: 0, total_removed_nodes: 1, retained_node_count: 0, total_added_edges: 0, total_removed_edges: 0, retained_edge_count: 0, added_nodes: [], removed_nodes: [{ id: 'old', path: 'removed.py', kind: 'file', evidence: { commit: sha } }], limitations: ['Fixture · DEMO'] } })
      if (path.endsWith('/graph')) {
        if (graphFailure && path.includes(target)) return route.fulfill({ status: 503, json: { code: 'explorer_unavailable' } })
        return route.fulfill({ json: { commit: path.includes(target) ? target : sha, nodes: [], edges: [], total_nodes: 0, total_edges: 0, truncated: false } })
      }
      return route.fulfill({ status: 404, json: { code: 'not_found' } })
    })
    await page.goto(`/app/projects/${project}/what-if`)
    await page.getByLabel('Base commit', { exact: true }).fill(sha)
    await page.getByLabel('Target commit', { exact: true }).fill(target)
    await page.getByRole('button', { name: 'So sánh graph phiên bản', exact: true }).click()
    if (graphFailure) {
      await expect(page.getByRole('alert')).toBeVisible()
      await expect(page.getByRole('heading', { name: 'Thay đổi cấu trúc graph', exact: true })).toHaveCount(0)
      await expect(page.locator('.comparison-graphs')).toHaveCount(0)
    } else {
      await expect(page.getByRole('heading', { name: 'Thay đổi cấu trúc graph', exact: true })).toBeVisible()
      await expect(page.getByText('removed.py · bằng chứng base', { exact: true })).toBeVisible()
      await expect(page.getByRole('heading', { name: `Base ${sha}`, exact: true })).toBeVisible()
      await expect(page.getByRole('heading', { name: `Target ${target}`, exact: true })).toBeVisible()
    }
  })
}
