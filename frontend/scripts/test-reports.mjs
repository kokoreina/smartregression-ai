import assert from 'node:assert/strict'
import { readFile, mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const root = new URL('../../', import.meta.url)
const output = new URL('var/frontend-report-tests/', root)
await mkdir(output, { recursive: true })
const source = new URL('frontend/src/features/reports/stageReportValidation.ts', root)
const compiled = ts.transpileModule(await readFile(source, 'utf8'), {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText
await writeFile(new URL('validation.mjs', output), compiled)
const { validateReportValue, readReportFile } = await import(new URL('validation.mjs', output).href)
const schema = JSON.parse(await readFile(new URL('contracts/generated/openapi.json', root), 'utf8'))
const validate = (value) => validateReportValue(value, schema.components.schemas)
let checks = 0
const rejected = []
const allowed = new Set(['$ref', 'additionalProperties', 'anyOf', 'const', 'default', 'enum', 'items', 'minItems', 'minLength', 'minimum', 'pattern', 'properties', 'required', 'title', 'type'])
const visited = new Set()
function checkKeywords(node) {
  for (const key of Object.keys(node)) assert(allowed.has(key), `Unsupported schema keyword: ${key}`)
  if (node.$ref && !visited.has(node.$ref)) {
    visited.add(node.$ref)
    checkKeywords(schema.components.schemas[node.$ref.split('/').at(-1)])
  }
  Object.values(node.properties ?? {}).forEach(checkKeywords)
  node.anyOf?.forEach(checkKeywords)
  if (node.items) checkKeywords(node.items)
}
checkKeywords(schema.components.schemas.StageAnalysisReport)
function rejects(report, mutate) {
  const value = structuredClone(report)
  mutate(value)
  assert.throws(() => validate(value))
  rejected.push(value)
  checks++
}
for (const variant of ['partial', 'empty', 'failed', 'not-implemented']) {
  const report = JSON.parse(await readFile(new URL(`examples/reports/stage-report.${variant}.json`, root), 'utf8'))
  assert.doesNotThrow(() => validate(report))
  checks++
  rejects(report, (r) => { r.identity.run_id = [] })
  rejects(report, (r) => { r.identity.target.repository_id = 'foreign' })
  rejects(report, (r) => { r.stages.changes = null })
  rejects(report, (r) => { r.stages.graph.extra = 'forbidden' })
  rejects(report, (r) => { r.analysis_status = r.analysis_status === 'completed' ? 'failed' : 'completed' })
  rejects(report, (r) => { r.stages.inventory = { status: 'completed', data: null } })
  rejects(report, (r) => { r.stages.retrieval = { status: 'failed' } })
  rejects(report, (r) => { r.llm_cost_usd = -1 })
  rejects(report, (r) => { r.identity.base.commit += '\n' })
  rejects(report, (r) => { r.report_id = '\u0085' })
}
const partial = JSON.parse(await readFile(new URL('examples/reports/stage-report.partial.json', root), 'utf8'))
rejects(partial, (r) => { r.stages.evidence.data.items[0].location.line_end = 0 })
rejects(partial, (r) => { r.stages.evidence.data.items[0].path = '../private' })
rejects(partial, (r) => { r.stages.evidence.data.items[0].snapshot.commit = 'b'.repeat(40) })
rejects(partial, (r) => { r.stages.evidence.data.items[0].location.line_start = 999 })
rejects(partial, (r) => { r.stages.evidence.data.items[0].support = 'supported'; r.stages.evidence.data.items[0].resolution = 'missing' })
rejects(partial, (r) => { r.identity.run_id = '  ' })
rejects(partial, (r) => { r.stages.evidence.data.items[0].path = '.git/config' })
rejects(partial, (r) => { r.stages.evidence.data.items[0].path = 'src/conin$.py' })
rejects(partial, (r) => { r.stages.evidence.data.items[0].path = 'src/ leading.py' })
rejects(partial, (r) => { r.stages.graph.data.edges[0].target = 'unknown.py' })
rejects(partial, (r) => { r.stages.graph.data.nodes.push('a.py') })
rejects(partial, (r) => { r.stages.impact.data.paths[0].nodes.reverse() })
rejects(partial, (r) => { r.stages.impact.data.candidates[0].changed_component_id = 'unknown' })
rejects(partial, (r) => { r.stages.impact.data.candidates[0].path_ids = ['unknown'] })
rejects(partial, (r) => { r.stages.impact.data.candidates[0].evidence_ids = ['unknown'] })
rejects(partial, (r) => { r.stages.review_ordering.data.candidates[0].path = 'unknown.py' })
rejects(partial, (r) => { r.stages.changes.data.files = [] })
rejects(partial, (r) => { r.stages.changes.data.components[0].change = 'renamed' })
rejects(partial, (r) => { r.stages.changes.data.components[2].target_location = null })
rejects(partial, (r) => { r.stages.evidence.data.items.push(r.stages.evidence.data.items[0]) })
rejects(partial, (r) => {
  r.stages.impact.data.candidates[0].evidence_ids = []
  r.stages.evidence.data.items[1].id = ` ${r.stages.evidence.data.items[0].id} `
})
rejects(partial, (r) => { r.stages.evidence.limitations = [] })
rejects(partial, (r) => { r.stages.graph.limitations = [{ code: 'unresolved_import' }] })
// Reference and native-ID cases include legal defaults and empty results.
const withContext = structuredClone(partial)
const snapshot = withContext.identity.target
const sourceIdentity = { snapshot, index_id: 'index-fixture', configuration_id: 'config-fixture' }
withContext.stages.inventory = {
  status: 'completed',
  data: { snapshot, framework: 'pytest', completeness: 'complete', test_ids: ['test/a.py::test_x[ space ]'] },
}
withContext.stages.retrieval = {
  status: 'completed',
  data: { sources: [sourceIdentity], items: [{
    ...sourceIdentity, id: 'chunk-fixture', path: 'a.py', location: { line_start: 1, line_end: 2 },
    content_sha256: 'a'.repeat(64), rank: 1,
  }] },
}
validate(withContext)
checks++
const spacedMetadata = structuredClone(withContext)
spacedMetadata.identity.run_id = ` ${withContext.identity.run_id} `
spacedMetadata.stages.impact.data.paths[0].changed_component_id = ` ${spacedMetadata.stages.impact.data.paths[0].changed_component_id} `
spacedMetadata.stages.impact.data.candidates[0].evidence_ids = spacedMetadata.stages.impact.data.candidates[0].evidence_ids.map((id) => ` ${id} `)
validate(spacedMetadata)
assert.equal(spacedMetadata.identity.run_id, withContext.identity.run_id)
assert.deepEqual(spacedMetadata.stages.inventory.data.test_ids, withContext.stages.inventory.data.test_ids)
checks++
const unicodeMetadata = structuredClone(withContext)
unicodeMetadata.report_id = '\ufeffreport\ufeff'
unicodeMetadata.identity.run_id = `\u0085${withContext.identity.run_id}\u0085`
validate(unicodeMetadata)
assert.equal(unicodeMetadata.report_id, '\ufeffreport\ufeff')
assert.equal(unicodeMetadata.identity.run_id, withContext.identity.run_id)
checks++
rejects(withContext, (r) => { r.stages.retrieval.data.items[0].configuration_id = 'foreign' })
rejects(withContext, (r) => { r.stages.retrieval.data.items[0].snapshot = r.identity.base })
rejects(withContext, (r) => { r.stages.retrieval.data.sources[0].snapshot = { ...r.identity.target, snapshot_id: null } })
rejects(withContext, (r) => { r.stages.retrieval.data.items.push({ ...r.stages.retrieval.data.items[0], id: 'second' }) })
rejects(withContext, (r) => { r.stages.retrieval.data.items[0].content_sha256 = 'wrong' })
rejects(withContext, (r) => { r.stages.inventory.data.snapshot = r.identity.base })
rejects(withContext, (r) => { r.stages.inventory.data.test_ids.push(r.stages.inventory.data.test_ids[0]) })
rejects(withContext, (r) => { r.stages.inventory.data.completeness = 'partial' })
const emptyContext = structuredClone(withContext)
emptyContext.stages.retrieval.data.items = []
emptyContext.stages.inventory.data.test_ids = []
validate(emptyContext)
checks++
const defaultFields = structuredClone(partial)
for (const stage of Object.values(defaultFields.stages)) {
  for (const key of ['data', 'reason', 'error_code']) if (stage[key] === null) delete stage[key]
  if (stage.limitations.length === 0) delete stage.limitations
}
delete defaultFields.stages.graph.data.edge_direction
delete defaultFields.analysis_duration_seconds
delete defaultFields.llm_cost_usd
validate(defaultFields)
checks++
const poisoned = structuredClone(partial)
poisoned.identity.run_id = { private_input_marker: 'do-not-echo-this' }
assert.throws(() => validate(poisoned), (error) => !error.message.includes('do-not-echo-this'))
checks++
await writeFile(new URL('rejected.json', output), JSON.stringify(rejected))
const file = new File([JSON.stringify(withContext)], 'valid.json', { type: 'application/json' })
assert.deepEqual(await readReportFile(file, schema.components.schemas), withContext)
await assert.rejects(readReportFile(new File(['{"private_marker":'], 'broken.json'), schema.components.schemas),
  (error) => !error.message.includes('private_marker'))
await assert.rejects(readReportFile(new File(['{}'], 'invalid.json'), schema.components.schemas))
const oversized = new File([new Uint8Array(16 * 1024 * 1024 + 1)], 'oversized.json')
oversized.text = () => { throw new Error('size must be checked before reading') }
await assert.rejects(readReportFile(oversized, schema.components.schemas), /16 MiB/u)
checks += 4
// v3 has explicit proposal/selection/execution semantics. The current v2 UI
// must reject it rather than render a source-analysis projection as the full run.
for (const variant of ['proposal', 'provider-error', 'not-run']) {
  const report = JSON.parse(await readFile(new URL(`examples/reports/workflow-report.${variant}.json`, root), 'utf8'))
  assert.throws(() => validate(report))
  checks++
}
// Actual reports are optional inputs; their bytes stay local and must pass the same boundary.
for (const file of process.argv.slice(2)) {
  validate(JSON.parse(await readFile(fileURLToPath(new URL(file, root)), 'utf8')))
  checks++
}
console.log(`${checks} report validation checks passed`)
