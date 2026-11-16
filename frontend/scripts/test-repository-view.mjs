/** Real public report/fixture rendering and consumer guards; not browser acceptance. */
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

const root = new URL('../', import.meta.url)
const server = await createServer({ root: fileURLToPath(root), configFile: false,
  cacheDir: fileURLToPath(new URL('node_modules/.vite-repository-ssr', root)),
  optimizeDeps: { noDiscovery: true, include: [] },
  server: { middlewareMode: true, hmr: false, watch: null }, esbuild: { jsx: 'automatic' } })
let checks = 0
try {
  const { RepositoryAnalysis, RepositoryResult } = await server.ssrLoadModule('/src/features/repositories/RepositoryAnalysis.tsx')
  const { analysisValue, post, messages } = await server.ssrLoadModule('/src/features/repositories/repositoryClient.ts')
  const { treeValue, buildTree, filterTree, treeText } = await server.ssrLoadModule('/src/features/repositories/repositoryTree.ts')
  const { RepositoryTreeView } = await server.ssrLoadModule('/src/features/repositories/RepositoryTreeView.tsx')
  const tree = { schema_version: '1.0.0', repository_url: 'https://github.com/owner/repo',
    commit: 'a'.repeat(40), tree_sha: 'b'.repeat(40), entries: [
      { path: 'README.md', kind: 'file', size: 20 },
      { path: 'src/App.js', kind: 'file', size: 42 },
      { path: 'src', kind: 'directory', size: null },
      { path: 'demo.mov', kind: 'file', size: 51384541 },
      { path: 'node_modules', kind: 'submodule', size: null },
    ] }
  assert.equal(treeValue(tree, tree.repository_url, tree.commit), tree)
  const nodes = buildTree(tree.entries)
  assert.equal(treeText(nodes, 'repo'), 'repo/\n├── src/\n│   └── App.js\n├── README.md\n├── demo.mov\n└── node_modules [submodule]\n')
  assert.equal(filterTree(nodes, 'App.js')[0].children[0].path, 'src/App.js')
  assert.equal(filterTree(nodes, 'not-found').length, 0)
  const treeHtml = renderToStaticMarkup(createElement(RepositoryTreeView, { tree }))
  assert(treeHtml.includes('Cây thư mục dự án') && treeHtml.includes('App.js') && treeHtml.includes('Tải cây dạng văn bản'))
  assert(treeHtml.includes('Thư mục src') && treeHtml.includes('tree-search'))
  checks += 6
  for (const mutate of [t => { t.commit = 'c'.repeat(40) }, t => { t.repository_url = 'https://attacker.test' },
    t => { t.entries.push(t.entries[0]) }, t => { t.entries[1].path = '../escape' },
    t => { t.entries[2].kind = 'file'; t.entries[2].size = 1 },
    t => { t.entries[0].size = -1 }, t => { t.entries[1].path = 'missing/App.js' }]) {
    const bad = structuredClone(tree)
    mutate(bad)
    assert.throws(() => treeValue(bad, tree.repository_url, tree.commit))
    checks++
  }
  const escapedTree = structuredClone(tree)
  escapedTree.entries[0].path = '<img src=x onerror=alert(1)>'
  const escaped = renderToStaticMarkup(createElement(RepositoryTreeView, { tree: treeValue(escapedTree, tree.repository_url, tree.commit) }))
  assert(escaped.includes('&lt;img') && !escaped.includes('<img src=x'))
  checks++
  const originalFetch = globalThis.fetch
  try {
    for (const code of ['github_rate_limit', 'github_timeout', 'repository_limit', 'snapshot_acquisition_failed']) {
      globalThis.fetch = async () => new Response(JSON.stringify({ schema_version: '1.0.0', code: 'http_422', message: code }), { status: 422 })
      await assert.rejects(post('/repository-analyses', {}, new AbortController().signal), { message: messages[code] })
      checks++
    }
    globalThis.fetch = async () => new Response(JSON.stringify({ code: 'http_500', message: 'private transport details' }), { status: 500 })
    await assert.rejects(post('/repository-analyses', {}, new AbortController().signal), error => !error.message.includes('private transport details'))
    checks++
    globalThis.fetch = async () => new Response('<html>proxy error</html>', { status: 502 })
    await assert.rejects(post('/repository-analyses', {}, new AbortController().signal), /Backend chưa trả JSON/)
    checks++
    globalThis.fetch = async () => { throw new TypeError('private connection details') }
    await assert.rejects(post('/repositories/inspect', {}, new AbortController().signal), /Không kết nối được API/)
    checks++
  } finally {
    globalThis.fetch = originalFetch
  }
  const html = renderToStaticMarkup(createElement(RepositoryAnalysis))
  assert(html.includes('repository-url') && html.includes('Đọc repository'))
  assert(html.includes('https://github.com/andialbrecht/sqlparse'))
  checks += 2
  const report = JSON.parse(await readFile(new URL('../../examples/reports/stage-report.partial.json', import.meta.url), 'utf8'))
  const sample = { schema_version: '1.0.0', repository: { schema_version: '1.0.0',
    repository_url: 'https://github.com/owner/repo', full_name: 'owner/repo', default_branch: 'main', commits: [] },
    report, files: ['app.py'], narrative_evidence: [{ id: 'change-0', path: 'app.py' }],
    narrative: { status: 'completed', data: { summary: '<img src=x onerror=alert(1)>',
      findings: [{ path: 'app.py', explanation: 'Potential impact only.', evidence_ids: ['change-0'] }], limitations: [] } },
    selection_status: 'not_run', execution_status: 'not_run', limitations: ['No execution.'] }
  const { exportReport, loadRepositoryReport } = await server.ssrLoadModule('/src/features/repositories/repositoryReport.ts')
  const exported = exportReport(sample, '2026-11-15T12:00:00Z')
  const saved = await loadRepositoryReport(new File([JSON.stringify(exported)], 'analysis.json'))
  assert.deepEqual(saved.result, sample)
  assert.equal(saved.exportedAt, '2026-11-15T12:00:00Z')
  const legacy = await loadRepositoryReport(new File([JSON.stringify(sample)], 'legacy.json'))
  assert.equal(legacy.exportedAt, null)
  assert.deepEqual(legacy.result.narrative, sample.narrative)
  await assert.rejects(loadRepositoryReport(new File(['{broken'], 'broken.json')))
  let readOversized = false
  await assert.rejects(loadRepositoryReport({ size: 16 * 1024 * 1024 + 1, text() { readOversized = true } }))
  assert.equal(readOversized, false)
  for (const mutate of [v => { v.schema_version = 'future' }, v => { v.report_kind = 'other' },
    v => { v.exported_at = '2026-11-15T12:00:00' }, v => { v.exported_at = '2026-99-99T12:00:00Z' },
    v => { v.exported_at = '2026-02-30T12:00:00Z' },
    v => { v.payload.narrative.data.findings[0].evidence_ids = ['invented'] },
    v => { v.payload.narrative_evidence[0].symbol = {} }, v => { v.payload.narrative.status = 'failed' },
    v => { v.payload.files.push('app.py') }, v => { v.payload.narrative.data.findings[0].evidence_ids = Array(9).fill('change-0') }]) {
    const bad = structuredClone(exported)
    mutate(bad)
    await assert.rejects(loadRepositoryReport(new File([JSON.stringify(bad)], 'bad.json')))
    checks++
  }
  const { createHash } = await import('node:crypto')
  const real = structuredClone(sample)
  real.report.data_kind = 'real'
  const repositoryId = 'github-' + createHash('sha256').update('owner/repo').digest('hex')
  function bindIdentity(value) {
    if (!value || typeof value !== 'object') return
    for (const [key, child] of Object.entries(value)) {
      if (key === 'repository_id') value[key] = repositoryId
      else bindIdentity(child)
    }
  }
  bindIdentity(real.report)
  assert.equal((await loadRepositoryReport(new File([JSON.stringify(real)], 'real.json'))).result.report.data_kind, 'real')
  real.repository.repository_url = 'https://github.com/other/repo'
  real.repository.full_name = 'other/repo'
  await assert.rejects(loadRepositoryReport(new File([JSON.stringify(real)], 'wrong-repo.json')), /định danh repository/)
  checks += 2
  for (const mutate of [s => { s.narrative.reason = 'disabled' },
    s => { s.repository.full_name = 'another/repo' },
    s => { s.narrative.status = 'not_run'; s.narrative.data = null; s.narrative.error_code = 'provider_quota' },
    s => { s.narrative.status = 'failed'; s.narrative.data = null; s.narrative.error_code = 'invented' },
    s => { s.narrative.usage = { total_tokens: 1.5 } },
    s => { s.narrative.usage = { fabricated_cost: 0 } }]) {
    const bad = structuredClone(sample)
    mutate(bad)
    assert.throws(() => analysisValue(bad))
    checks++
  }
  checks += 7
  const render = value => renderToStaticMarkup(createElement(RepositoryResult, { result: analysisValue(value), onDownload() {} }))
  const output = render(sample)
  assert(output.includes('&lt;img') && !output.includes('<img src=x'))
  assert(output.includes('change-0') && output.includes('focus-changed-file'))
  assert(output.includes('href="#metadata-change-0"') && output.includes('id="metadata-change-0"'))
  const replay = renderToStaticMarkup(createElement(RepositoryResult, { result: sample, onDownload() {}, saved: true, exportedAt: saved.exportedAt }))
  assert(replay.includes('Báo cáo đã lưu') && replay.includes('Thời điểm xuất'))
  checks += 4
  for (const mutate of [s => { s.schema_version = 'bad' }, s => { s.execution_status = 'completed' },
    s => { s.narrative.data.findings[0].evidence_ids = ['invented'] }, s => { s.narrative.status = 'invented' },
    s => { s.narrative.data.findings[0].path = 'other.py' },
    s => { s.narrative.model = {} }, s => { s.narrative.usage = { total_tokens: -1 } },
    s => { s.narrative_evidence.push({ id: 'change-0', path: 'app.py' }) }]) {
    const bad = structuredClone(sample)
    mutate(bad)
    assert.throws(() => analysisValue(bad))
    checks++
  }
  for (const path of process.argv.slice(2)) {
    const actual = JSON.parse(await readFile(new URL(path, new URL('../../', import.meta.url)), 'utf8'))
    assert.equal(actual.report.data_kind, 'real')
    const rendered = render(actual)
    assert(rendered.includes(actual.repository.full_name))
    assert(rendered.includes(actual.report.identity.target.commit))
    const reopened = await loadRepositoryReport(new File([JSON.stringify(exportReport(actual))], 'actual.json'))
    assert.deepEqual(reopened.result.narrative, actual.narrative)
    assert.deepEqual(reopened.result.report.identity, actual.report.identity)
    checks++
  }
} finally {
  await server.close()
}
console.log(`${checks} repository UI/consumer checks passed (SSR, not browser)`)
