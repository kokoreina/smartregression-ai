/** Server-rendered component regressions; this does not replace browser acceptance. */
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

const root = new URL('../', import.meta.url)
const server = await createServer({
  root: fileURLToPath(root), configFile: false,
  server: { middlewareMode: true, hmr: false, watch: null },
  esbuild: { jsx: 'automatic' },
})
let checks = 0
try {
  const { StageReportView } = await server.ssrLoadModule('/src/features/reports/StageReportView.tsx')
  const { validateStageReport } = await server.ssrLoadModule('/src/features/reports/stageReport.ts')
  const fixture = async (name) => JSON.parse(await readFile(new URL(`../examples/reports/stage-report.${name}.json`, root), 'utf8'))
  const render = (report) => renderToStaticMarkup(createElement(StageReportView, { report: validateStageReport(report) }))
  const partial = await fixture('partial')
  const html = render(partial)
  assert(html.includes(`Run ID: <code>${partial.identity.run_id}</code>`))
  assert(html.includes(`Report ID: <code>${partial.report_id}</code>`))
  assert(html.includes('DEMO') && html.includes('not_verified'))
  assert(html.includes(partial.identity.base.commit) && html.includes(partial.identity.target.commit))
  assert(html.includes('chưa đo'))
  checks += 5
  const docs = await fixture('empty')
  docs.stages.changes.data.files = [{ path: 'docs/guide.md', status: 'file_only', limitations: ['unsupported_extension'] }]
  docs.stages.changes.data.components = [{ id: 'docs-fixture', path: 'docs/guide.md', kind: 'file', change: 'modified', reason: 'file_metadata' }]
  for (const name of ['changes', 'impact', 'review_ordering']) {
    docs.stages[name].status = 'partial'
    docs.stages[name].limitations = [{ code: 'unsupported_extension', path: 'docs/guide.md' }]
  }
  docs.analysis_status = 'partial'
  const docsHtml = render(docs)
  assert(docsHtml.includes('docs/guide.md') && docsHtml.includes('unsupported_extension'))
  checks++
  for (const variant of ['empty', 'failed', 'not-implemented']) {
    const report = await fixture(variant)
    assert.doesNotThrow(() => render(report))
    checks++
  }
  const escaped = structuredClone(partial)
  escaped.report_id = '<img src=x onerror=alert(1)>'
  const escapedHtml = render(escaped)
  assert(!escapedHtml.includes('<img') && escapedHtml.includes('&lt;img'))
  checks++
  for (const file of process.argv.slice(2)) {
    const report = JSON.parse(await readFile(new URL(file, new URL('../', root)), 'utf8'))
    const actual = render(report)
    assert(actual.includes('REAL') && actual.includes(report.identity.run_id))
    for (const item of report.stages.retrieval.data.items) {
      assert(actual.includes(item.content_sha256) && actual.includes(item.snapshot.commit))
      assert(actual.includes(item.index_id) && actual.includes(item.configuration_id))
    }
    checks++
  }
} finally {
  await server.close()
}
console.log(`${checks} server-rendered report checks passed (browser still required)`)
