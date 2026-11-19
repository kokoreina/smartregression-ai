import { test, expect } from '@playwright/test'

const projectId = '11111111-1111-4111-8111-111111111111'
const projectPath = `/app/projects/${projectId}`
const latest = 'a'.repeat(40)
const previous = 'b'.repeat(40)
const repository = 'https://github.com/example/ui-fixture'
const coverage = { status: 'complete', analyzed_files: ['app.py', 'utils.py'], unparsed_files: [], unsupported_files: [] }

test('coverage explains parse success, file kinds, unknown relations and classified references separately', async ({ page }) => {
  await fixture(page, { coverage: { ...coverage, status: 'partial', unsupported_files: ['README.md', 'pytest.ini', 'app.ts'], diagnostics: {
    file_groups: { documentation_asset: ['README.md'], configuration: ['pytest.ini'], other_unsupported: ['app.ts'] },
    unresolved_by_reason: { unresolved_internal_import: 1, unresolved_static_call: 2 },
    classified_by_kind: { builtin_call: 5, stdlib_import: 1 }, excluded_files: ['pytest.ini'],
  } } })
  await page.goto(projectPath)
  const scope = page.locator('.coverage-details').first()
  await expect(scope).toContainText('File không đọc được cú pháp0')
  await scope.getByText('3 trường hợp chưa xác định · xem nguyên nhân', { exact: true }).click()
  await expect(scope.getByText('Import nội bộ chưa tìm được đích', { exact: true })).toBeVisible()
  await expect(scope.getByText('Lời gọi built-in Python nhận diện được', { exact: true })).toBeVisible()
  await expect(scope).toContainText('toàn snapshot')
  await scope.getByText('File nào chưa được phân tích?', { exact: true }).click()
  await scope.getByText('Cấu hình/dependency (1)', { exact: true }).click()
  await expect(scope.getByText('pytest.ini', { exact: true })).toBeVisible()
  await expect(scope).toContainText('vẫn có thể thay đổi cách chạy test')
  for (const width of [1440, 1024, 768, 375, 320]) {
    await page.setViewportSize({ width, height: 1000 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true)
  }
})

test('legacy snapshot coverage never invents a diagnostic breakdown', async ({ page }) => {
  await fixture(page, { coverage: { ...coverage, status: 'partial', unsupported_files: ['pytest.ini'] } })
  await page.goto(projectPath)
  const scope = page.locator('.coverage-details').first()
  await scope.getByText('Vì sao snapshot còn giới hạn?', { exact: true }).click()
  await expect(scope).toContainText('Snapshot cũ chưa có phân loại chi tiết')
  await expect(scope.locator('.coverage-reasons')).toHaveCount(0)
})

test('impact overview uses returned counts and actual propagation paths without new analysis', async ({ page }) => {
  const calls = await fixture(page, { impact: { changed: ['app.py'], direct: ['utils.py'], indirect: [], denominator: 2, percentages: { changed: 50, direct: 50, indirect: 0 }, counts: { changed: 1, direct: 1, indirect: 0 }, unknown_changed_count: 0, paths: { 'utils.py': ['app.py', 'utils.py'] }, coverage: { ...coverage, status: 'partial', unsupported_files: ['asset.css'] }, unresolved_count: 3, paths_truncated: true } })
  await page.goto(projectPath)
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  const overview = page.getByRole('region', { name: 'Ảnh hưởng tiềm năng theo phân tích tĩnh', exact: true })
  await expect(overview).toContainText('So với 2 file phân tích được')
  await expect(overview.locator('.impact-group-changed')).toContainText('File giả định thay đổi')
  await expect(overview).toContainText('không phải kết quả so sánh hai commit')
  await expect(overview.locator('.impact-group-direct')).toContainText('1 file')
  await expect(overview.locator('.impact-group-direct')).toContainText('50%')
  await expect(overview).toContainText('3 quan hệ chưa giải được')
  await expect(overview).toContainText('Đường lan truyền đã giới hạn')
  await page.setViewportSize({ width: 1440, height: 1800 })
  await overview.evaluate(element => element.scrollIntoView({ block: 'center' }))
  await overview.screenshot({ path: '../var/task-3.48/impact-overview-synthetic.png' })
  const chain = overview.getByRole('list', { name: 'Chuỗi lan truyền ảnh hưởng' })
  await expect(chain.getByRole('listitem')).toHaveCount(2)
  await expect(chain.getByRole('button', { name: 'app.py', exact: true })).toBeVisible()
  await chain.getByRole('button', { name: 'utils.py', exact: true }).click()
  await expect(page).toHaveURL(/path=utils.py/)
  expect(calls.snapshots).toHaveLength(1)
  expect(calls.ai).toBe(0)
  for (const width of [1440, 1024, 768, 375]) {
    await page.setViewportSize({ width, height: 1000 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true)
  }
})

test('unmeasured impact stays unknown and never draws a zero-percent bar', async ({ page }) => {
  await fixture(page, { impact: { changed: ['app.py'], direct: [], indirect: [], denominator: null, percentages: { changed: null, direct: null, indirect: null }, counts: {}, unknown_changed_count: 1, paths: {}, coverage: { status: 'partial', analyzed_files: [], unparsed_files: ['app.py'], unsupported_files: [] }, unresolved_count: 0 } })
  await page.goto(projectPath)
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  const overview = page.getByRole('region', { name: 'Ảnh hưởng tiềm năng theo phân tích tĩnh', exact: true })
  await expect(overview).toContainText('số file chưa xác định')
  await expect(overview.getByText('Chưa đo', { exact: true })).toHaveCount(3)
  await expect(overview.locator('.impact-comparison-track')).toHaveCount(0)
  await expect(overview.locator('.impact-propagation')).toHaveCount(0)
})

for (const kind of ['static_overlay', 'hypothesis']) {
  test(`saved what-if visualizes only measured static results: ${kind}`, async ({ page }) => {
    const calls = await fixture(page)
    const scenarioId = '22222222-2222-4222-8222-222222222222'
    await page.route(`**/api/v1/projects/${projectId}/scenarios/${scenarioId}`, route => route.fulfill({ json: {
      id: scenarioId, project_id: projectId, baseline: latest, config_digest: 'c'.repeat(64), input_digest: 'e'.repeat(64), title: 'What-if fixture · DEMO', path: 'app.py', mode: kind === 'hypothesis' ? 'description' : 'code', created_at: '2026-11-17T00:00:00Z', analysis_kind: kind,
      impact: kind === 'hypothesis' ? null : { changed: ['app.py'], direct: ['utils.py'], indirect: [], denominator: 2, counts: { changed: 1, direct: 1, indirect: 0, potential: 2 }, percentages: { changed: 50, direct: 50, indirect: 0, potential: 100 }, paths: { 'utils.py': ['app.py', 'utils.py'] }, unknown_changed_count: 0, unresolved_count: 0, coverage },
      added_symbols: [], removed_symbols: [], added_node_count: kind === 'hypothesis' ? null : 0, removed_node_count: kind === 'hypothesis' ? null : 0, added_edge_count: kind === 'hypothesis' ? null : 0, removed_edge_count: kind === 'hypothesis' ? null : 0, limitations: ['Dữ liệu fixture · DEMO'],
    } }))
    await page.goto(`${projectPath}/scenarios/${scenarioId}`)
    await expect(page.getByRole('heading', { name: 'What-if fixture · DEMO' })).toBeVisible()
    if (kind === 'static_overlay') {
      await expect(page.getByRole('region', { name: 'Ảnh hưởng tiềm năng trong overlay' })).toBeVisible()
      await expect(page.getByText('Phạm vi tiềm năng: 100%', { exact: false })).toBeVisible()
      await expect(page.getByRole('list', { name: 'Chuỗi lan truyền ảnh hưởng' }).getByRole('listitem')).toHaveCount(2)
    } else {
      await expect(page.getByText('GIẢ THUYẾT — chưa phải code đã thay đổi')).toBeVisible()
      await expect(page.locator('.impact-overview')).toHaveCount(0)
    }
    expect(calls.snapshots).toHaveLength(0)
    expect(calls.ai).toBe(0)
  })
}

async function fixture(page, options = {}) {
  const calls = { snapshots: [], impact: [], ai: 0 }
  await page.route('**/api/v1/**', async route => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace('/api/v1', '')
    const commit = path.includes(previous) ? previous : latest
    const respond = (body, status = 200) => route.fulfill({ status, json: body })
    if (path.includes('/ai') && request.method() === 'POST') calls.ai++
    if (path.includes('/assistance/ai') && request.method() === 'GET') return respond([])
    if (path === '/capabilities') return respond({ local_demo: false })
    if (path === '/auth/me') return respond({ schema_version: '1.0.0', id: projectId, email: 'fixture@example.com', display_name: 'Kiểm thử UI · DEMO', verified: true })
    if (path === '/auth/csrf') return respond({ token: 'synthetic-csrf-token' })
    if (path === `/projects/${projectId}`) return respond({ schema_version: '1.0.0', id: projectId, title: 'Repository kiểm thử · DEMO', description: 'Dữ liệu giả dành riêng cho regression UI.', repository_url: repository, archived: false, version: 1, created_at: '2026-11-17T00:00:00Z', updated_at: '2026-11-17T00:00:00Z' })
    if (path.endsWith('/view-state')) {
      if (options.failSavedState) return respond({ code: 'project_storage_unavailable' }, 503)
      if (request.method() === 'PUT') return respond({ ...request.postDataJSON(), version: 2 })
      return respond(options.savedState ?? null)
    }
    if (path.endsWith('/repository')) return respond({ schema_version: '1.0.0', repository_url: repository, full_name: 'example/ui-fixture', default_branch: 'main', commits: [{ sha: latest, message: 'Synthetic latest commit', date: '2026-11-17T00:00:00Z' }] })
    if (path.endsWith('/snapshots')) {
      calls.snapshots.push(request.postDataJSON().commit)
      return respond({ commit: latest, config_digest: 'c'.repeat(64), coverage, total_nodes: 2, total_edges: 0, tree_entries: 2, excluded_count: 0 })
    }
    if (path.endsWith('/tree')) return options.failTree
      ? respond({ code: 'snapshot_not_ready' }, 409)
      : respond({ schema_version: '1.0.0', repository_url: repository, commit, tree_sha: 'd'.repeat(40), entries: [{ path: 'app.py', kind: 'file', size: 40 }, { path: 'utils.py', kind: 'file', size: 20 }] })
    if (path.endsWith('/graph')) return options.failGraph
      ? respond({ code: 'explorer_unavailable' }, 503)
      : respond({ repository_id: 'example/ui-fixture', commit, config_digest: 'c'.repeat(64), coverage: options.coverage ?? coverage, nodes: [{ id: '1'.repeat(64), path: 'app.py', kind: 'file', label: 'app.py', symbol: null, evidence: null }, { id: '2'.repeat(64), path: 'utils.py', kind: 'file', label: 'utils.py', symbol: null, evidence: null }], edges: [], total_nodes: 2, total_edges: 0, truncated: false })
    if (path.endsWith('/hotspots')) return options.failHotspots ? respond({ code: 'explorer_unavailable' }, 503) : respond({ cycles: [], fan_in: {}, fan_out: {}, cross_module_edges: [] })
    if (path.endsWith('/nodes')) return respond([])
    if (path.endsWith('/impact')) {
      calls.impact.push(url.searchParams.get('path'))
      return options.failImpact ? respond({ code: 'explorer_unavailable' }, 503) : respond(options.impact ?? { changed: [url.searchParams.get('path')], direct: ['utils.py'], indirect: [], denominator: 2, percentages: { changed: 50, direct: 50, indirect: 0 }, counts: { changed: 1, direct: 1, indirect: 0 }, unknown_changed_count: 0, paths: {}, coverage, unresolved_count: 0, interpretation: 'potential_static_impact' })
    }
    if (path.endsWith('/reading-guide')) return respond({ entrypoint_status: 'unknown', steps: [], limitations: [] })
    if (path.endsWith('/notes') || path.endsWith('/activity') || path.endsWith('/runs')) return respond({ items: [], next_cursor: null })
    return respond({ code: 'not_found' }, 404)
  })
  return calls
}

test('opening a project shows the tree and file impact without entering a SHA', async ({ page }) => {
  const calls = await fixture(page)
  await page.goto(projectPath)
  await expect(page.getByRole('region', { name: 'Cấu trúc thư mục' })).toBeVisible()
  await expect(page.getByLabel('Phiên bản mã nguồn')).toHaveValue(latest)
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
  await expect(page.locator('.explorer-inspector')).toContainText('utils.py')
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
  await expect(page.locator('.explorer-inspector')).not.toContainText('Đang đọc ảnh hưởng')
  expect(calls.snapshots).toEqual([latest])
  expect(calls.impact).toContain('app.py')
  expect(calls.ai).toBe(0)
})

for (const failure of ['failGraph', 'failHotspots']) {
  test(`tree remains usable when ${failure} fails`, async ({ page }) => {
    await fixture(page, { [failure]: true })
    await page.goto(`${projectPath}?commit=${latest}`)
    await expect(page.getByRole('region', { name: 'Cấu trúc thư mục' })).toBeVisible()
    await page.getByRole('button', { name: 'app.py', exact: true }).click()
    await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
    await expect(page.getByRole('alert')).toContainText('Một phần dữ liệu')
    if (failure === 'failHotspots') {
      await page.getByText('Hotspots cấu trúc', { exact: true }).click()
      await expect(page.getByText('Hotspots chưa tải được;', { exact: false })).toBeVisible()
      await expect(page.getByText('Không quan sát thấy vòng trong graph đã phân tích.')).toHaveCount(0)
    }
  })
}

test('a missing tree does not hide an available graph', async ({ page }) => {
  await fixture(page, { failTree: true })
  await page.goto(`${projectPath}?commit=${latest}`)
  await expect(page.locator('.react-flow')).toBeVisible()
  await expect(page.getByRole('alert')).toContainText('Một phần dữ liệu')
})

test('restoring a saved commit reads cache and never materializes latest', async ({ page }) => {
  const calls = await fixture(page, { savedState: { commit: previous, path: 'app.py', tab: 'details', focus_only: true, expanded_paths: [], version: 1 } })
  await page.goto(projectPath)
  await expect(page).toHaveURL(new RegExp(previous))
  await expect(page.getByLabel('Phiên bản mã nguồn')).toHaveValue(previous)
  await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
  expect(calls.snapshots).toEqual([])
})

test('an explicit commit link overrides saved state without reacquisition', async ({ page }) => {
  const calls = await fixture(page, { savedState: { commit: previous, path: null, tab: 'tree', focus_only: true, expanded_paths: [], version: 1 } })
  await page.goto(`${projectPath}?commit=${latest}`)
  await expect(page.getByRole('region', { name: 'Cấu trúc thư mục' })).toBeVisible()
  await expect(page).toHaveURL(new RegExp(latest))
  expect(calls.snapshots).toEqual([])
})

test('unavailable saved state does not silently replace it with latest', async ({ page }) => {
  const calls = await fixture(page, { failSavedState: true })
  await page.goto(projectPath)
  await expect(page.getByText('Chưa đọc được vị trí đã lưu.', { exact: false })).toBeVisible()
  await expect(page.getByLabel('Phiên bản mã nguồn')).toHaveValue(latest)
  expect(calls.snapshots).toEqual([])
})

test('file-impact failure is visible rather than an empty successful result', async ({ page }) => {
  await fixture(page, { failImpact: true })
  await page.goto(`${projectPath}?commit=${latest}`)
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  await expect(page.locator('.explorer-inspector [role=alert]')).toBeVisible()
  await expect(page.locator('.impact-metrics')).toHaveCount(0)
})

test('mobile selection opens Details and navigation supports Escape', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 850 })
  await fixture(page)
  await page.goto(projectPath)
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  await expect(page.locator('.explorer-inspector')).toBeVisible()
  await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
  await page.getByRole('button', { name: 'Mở điều hướng' }).click()
  await expect(page.locator('.workspace-sidebar')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.locator('.workspace-sidebar')).not.toBeVisible()
})

test('workspace reflows at five widths without document overflow', async ({ page }) => {
  await fixture(page)
  await page.goto(projectPath)
  await expect(page.getByRole('region', { name: 'Cấu trúc thư mục' })).toBeVisible()
  await page.setViewportSize({ width: 1152, height: 1000 })
  const tree = await page.locator('.explorer-tree').boundingBox()
  const inspector = await page.locator('.explorer-inspector').boundingBox()
  expect(inspector.y).toBeGreaterThan(tree.y)
  for (const width of [1440, 1280, 1024, 768, 375]) {
    await page.setViewportSize({ width, height: 1000 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `document overflow at ${width}px`).toBe(true)
    await page.screenshot({ path: `../var/uiux-playwright/workspace-${width}.png`, fullPage: true })
  }
})

test('dark explorer retains readable graph nodes, controls and file impact', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' })
  await fixture(page)
  await page.goto(projectPath)
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
  for (const panel of ['.explorer-tree', '.explorer-canvas', '.explorer-inspector']) {
    await expect(page.locator(panel)).toHaveCSS('background-color', 'rgb(24, 31, 43)')
    await expect(page.locator(panel)).toHaveCSS('color', 'rgb(233, 238, 245)')
  }
  await expect(page.locator('.react-flow__node').first()).toHaveCSS('background-color', 'rgb(35, 45, 61)')
  await expect(page.locator('.react-flow__node').first()).toHaveCSS('color', 'rgb(233, 238, 245)')
  await expect(page.locator('.react-flow__controls-button').first()).toHaveCSS('background-color', 'rgb(35, 45, 61)')
  await page.screenshot({ path: '../var/uiux-playwright/workspace-dark.png', fullPage: true })
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await expect(page.getByRole('button', { name: 'Mở phiên bản' })).toHaveCSS('transition-duration', '0s')
})

test('graph expansion and panel controls retain the selected file without new analysis', async ({ page }) => {
  const calls = await fixture(page)
  await page.goto(projectPath)
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
  const before = await page.locator('.graph-frame').boundingBox()
  await page.getByRole('button', { name: 'Mở rộng graph', exact: true }).click()
  await expect(page.locator('.explorer-tree')).not.toBeVisible()
  await expect(page.locator('.explorer-inspector')).not.toBeVisible()
  const expanded = await page.locator('.graph-frame').boundingBox()
  expect(expanded.width).toBeGreaterThan(before.width + 200)
  await page.locator('.react-flow__node').filter({ hasText: 'utils.py' }).click()
  await expect(page).toHaveURL(/path=utils\.py/)
  await expect(page.locator('.graph-selection-note')).toContainText('utils.py')
  await page.getByRole('button', { name: 'Chi tiết file', exact: true }).click()
  await expect(page.locator('.explorer-inspector')).toBeVisible()
  await expect(page.locator('.selected-path')).toHaveText('utils.py')
  await expect(page.locator('.explorer-inspector')).toContainText('Ảnh hưởng tiềm năng')
  await page.getByRole('group', { name: 'Bố trí không gian mã nguồn' }).getByRole('button', { name: 'Cây thư mục', exact: true }).click()
  await expect(page.locator('.explorer-tree')).not.toBeVisible()
  await page.getByRole('group', { name: 'Bố trí không gian mã nguồn' }).getByRole('button', { name: 'Cây thư mục', exact: true }).click()
  await expect(page.locator('.explorer-tree')).toBeVisible()
  await page.getByRole('button', { name: 'Mở rộng graph', exact: true }).click()
  await page.setViewportSize({ width: 375, height: 1000 })
  await page.getByRole('button', { name: 'Cây thư mục', exact: true }).click()
  await page.getByRole('button', { name: 'app.py', exact: true }).click()
  await expect(page.locator('.explorer-inspector')).toBeVisible()
  await expect(page.locator('.selected-path')).toHaveText('app.py')
  expect(calls.snapshots).toEqual([latest])
  expect(calls.ai).toBe(0)
})

test('graph display controls keep data and selection while hiding only visual clutter', async ({ page }) => {
  await fixture(page)
  await page.goto(projectPath)
  await expect(page.locator('.react-flow__node')).toHaveCount(2)
  await expect(page.getByRole('checkbox', { name: 'Nhãn quan hệ', exact: true })).not.toBeChecked()
  await page.getByRole('checkbox', { name: 'Nhãn quan hệ', exact: true }).check()
  await page.getByRole('checkbox', { name: 'Hiện thư mục', exact: true }).check()
  await page.getByRole('checkbox', { name: 'Hiện hàm và lớp', exact: true }).check()
  await expect(page.locator('.react-flow__node')).toHaveCount(2)
  await page.locator('.react-flow__node').filter({ hasText: 'app.py' }).click()
  await expect(page.locator('.selected-path')).toHaveText('app.py')
  const transformBefore = await page.locator('.react-flow__viewport').getAttribute('style')
  await page.getByRole('button', { name: 'Zoom In', exact: true }).click()
  await expect(page.locator('.react-flow__viewport')).not.toHaveAttribute('style', transformBefore)
  await page.getByRole('button', { name: 'Fit View', exact: true }).click()
  await expect(page.locator('.selected-path')).toHaveText('app.py')
})
