import type { StageAnalysisReport } from './stageReport'

type Schema = {
  $ref?: string; type?: string; const?: unknown; enum?: unknown[]; anyOf?: Schema[]
  properties?: Record<string, Schema>; required?: string[]; additionalProperties?: boolean
  items?: Schema; minItems?: number; minLength?: number; minimum?: number; pattern?: string
}

function requireValue(condition: unknown): asserts condition {
  if (!condition) throw new Error('Báo cáo sai cấu trúc, trạng thái hoặc tham chiếu định danh.')
}

// Pydantic Text uses Unicode White_Space. JS trim also removes BOM and misses
// NEL, which would change identifier equality and accept backend-invalid values.
const trimMetadata = (value: string) => value.replace(/^\p{White_Space}+|\p{White_Space}+$/gu, '')

export async function readReportFile(
  file: File,
  definitions: Record<string, unknown>,
): Promise<StageAnalysisReport> {
  if (file.size > 16 * 1024 * 1024) throw new Error('Báo cáo vượt giới hạn 16 MiB.')
  let raw: unknown
  try {
    raw = JSON.parse(await file.text())
  } catch {
    throw new Error('Không đọc được file JSON hợp lệ.')
  }
  validateReportValue(raw, definitions)
  return raw
}

/** Supported keywords are checked against the canonical generated schema in tests.
 * This is a bounded file-inspection boundary, not a general JSON Schema engine.
 */
export function validateReportValue(raw: unknown, definitions: Record<string, unknown>): asserts raw is StageAnalysisReport {
  let remaining = 250_000
  const schemas = definitions as Record<string, Schema>
  function matches(value: unknown, schema: Schema, depth = 0): boolean {
    requireValue(--remaining > 0 && depth < 64)
    if (schema.$ref) {
      const name = schema.$ref.replace('#/components/schemas/', '')
      const target = schemas[name]
      return !!target && matches(value, target, depth + 1)
    }
    if (schema.anyOf) return schema.anyOf.some((s) => matches(value, s, depth + 1))
    if ('const' in schema && value !== schema.const) return false
    if (schema.enum && !schema.enum.includes(value)) return false
    switch (schema.type) {
      case 'null': return value === null
      case 'string': return typeof value === 'string'
        && Array.from(value).length >= (schema.minLength ?? 0)
        && (!schema.pattern || new RegExp(schema.pattern, 'u').test(value))
      case 'integer': return typeof value === 'number' && Number.isSafeInteger(value) && value >= (schema.minimum ?? -Infinity)
      case 'number': return typeof value === 'number' && Number.isFinite(value) && value >= (schema.minimum ?? -Infinity)
      case 'array': return Array.isArray(value) && value.length >= (schema.minItems ?? 0)
        && !!schema.items && value.every((v) => matches(v, schema.items!, depth + 1))
      case 'object': {
        if (!value || typeof value !== 'object' || Array.isArray(value)) return false
        const object = value as Record<string, unknown>
        const properties = schema.properties ?? {}
        return (schema.required ?? []).every((key) => Object.hasOwn(object, key))
          && Object.entries(object).every(([key, v]) => properties[key]
            ? matches(v, properties[key], depth + 1) : schema.additionalProperties !== false)
      }
      default: return false
    }
  }
  requireValue(!!schemas.StageAnalysisReport && matches(raw, schemas.StageAnalysisReport))
  // The generated schema checks nested types. Model validators additionally
  // enforce relationships not expressible in that schema (backend stages.py).
  const report = raw as StageAnalysisReport
  const { identity, stages } = report
  type Snapshot = typeof identity.target
  const snapshotKey = (s: Snapshot) => [s.repository_id, s.commit, s.snapshot_id].join('/')
  const same = (a: Snapshot, b: Snapshot) => snapshotKey(a) === snapshotKey(b)
  const knownSnapshot = (s: Snapshot) => s.snapshot_id != null && (same(s, identity.base) || same(s, identity.target))
  const unique = (values: unknown[]) => requireValue(new Set(values.map((v) => JSON.stringify(v))).size === values.length)
  const path = (p: string) => requireValue(p.length > 0 && !/[\\:<>"|?*]/u.test(p)
    && !Array.from(p).some((c) => c.codePointAt(0)! < 32 || c.codePointAt(0) === 127)
    && !p.split('/').some((part) => !part || part === '.' || part === '..' || part.toLowerCase() === '.git'
      || part !== trimMetadata(part) || part.endsWith('.')
      || /^(con|prn|aux|nul|conin\$|conout\$|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)/iu.test(part)))
  function inspect(value: unknown): void {
    if (!value || typeof value !== 'object') return
    if (Array.isArray(value)) { value.forEach(inspect); return }
    const object = value as Record<string, unknown>
    if ('line_start' in object) requireValue(Number(object.line_start) <= Number(object.line_end))
    for (const [key, child] of Object.entries(object)) {
      // Match backend Text normalization before comparing identifiers. Framework
      // native test_ids stay opaque and must never be trimmed or normalized.
      if (['run_id', 'report_id', 'id', 'changed_component_id', 'index_id', 'configuration_id', 'rule_version', 'symbol', 'reason', 'explanation', 'excerpt', 'reference'].includes(key) && typeof child === 'string') {
        requireValue(trimMetadata(child).length > 0)
        object[key] = trimMetadata(child)
      }
      if (['path_ids', 'evidence_ids'].includes(key) && Array.isArray(child)) {
        object[key] = child.map((id: string) => { requireValue(trimMetadata(id).length > 0); return trimMetadata(id) })
      }
      if (['path', 'previous_path', 'source_path', 'source', 'target'].includes(key) && typeof child === 'string') path(child)
      if (key === 'nodes' && Array.isArray(child)) child.forEach((p: string) => path(p))
      inspect(child)
    }
  }
  inspect(report)
  requireValue(identity.base.repository_id === identity.repository_id && identity.target.repository_id === identity.repository_id)
  if (identity.base.commit === identity.target.commit && identity.base.snapshot_id && identity.target.snapshot_id) requireValue(same(identity.base, identity.target))
  const results = Object.values(stages)
  for (const stage of results) {
    const issues = stage.limitations ?? []
    if (stage.status === 'completed' || stage.status === 'partial') {
      requireValue(stage.data != null && stage.reason == null && stage.error_code == null)
      requireValue(stage.status === 'partial' ? issues.length > 0 : issues.length === 0)
    } else {
      requireValue(stage.data == null)
      requireValue(stage.status === 'failed' ? stage.error_code != null && stage.reason == null : stage.reason != null && stage.error_code == null)
    }
  }
  const statuses = results.map((s) => s.status)
  const expected = statuses.every((s) => s === 'completed') ? 'completed'
    : statuses.some((s) => s === 'completed' || s === 'partial') ? 'partial'
      : statuses.includes('failed') ? 'failed' : statuses.includes('not_run') ? 'not_run' : 'not_implemented'
  requireValue(report.analysis_status === expected)
  const changes = stages.changes.data, graph = stages.graph.data, impact = stages.impact.data
  if (stages.snapshots.data) requireValue(same(stages.snapshots.data.base, identity.base) && same(stages.snapshots.data.target, identity.target)
    && identity.base.snapshot_id != null && identity.target.snapshot_id != null)
  if (changes) {
    requireValue(identity.base.snapshot_id && identity.target.snapshot_id)
    unique(changes.components.map((c) => c.id)); unique(changes.files.map((f) => f.path))
    unique(changes.components.map((c) => [c.path, c.kind, c.symbol ?? null]))
    requireValue([...new Set(changes.components.map((c) => c.path))].sort().join('\0') === changes.files.map((f) => f.path).sort().join('\0'))
    for (const c of changes.components) {
      const symbolic = ['class', 'function', 'method'].includes(c.kind)
      requireValue(symbolic === (c.symbol != null))
      requireValue(c.previous_path == null || c.previous_path !== c.path)
      if (c.change === 'renamed') requireValue(c.previous_path != null)
      if (c.kind === 'file') requireValue(c.base_location == null && c.target_location == null)
      if (c.change === 'added') requireValue(c.base_location == null)
      if (c.change === 'deleted') requireValue(c.target_location == null)
      if (symbolic && c.change !== 'added') requireValue(c.base_location != null)
      if (symbolic && c.change !== 'deleted') requireValue(c.target_location != null)
    }
    for (const f of changes.files) if (f.status !== 'completed') requireValue(f.limitations.length > 0)
    if (changes.files.some((f) => f.status !== 'completed' || f.limitations.length)) requireValue(stages.changes.status === 'partial')
  }
  if (graph) {
    requireValue(knownSnapshot(graph.snapshot)); unique(graph.nodes)
    unique(graph.edges.map((e) => [e.source, e.target, e.kind]))
    requireValue(graph.edges.every((e) => graph.nodes.includes(e.source) && graph.nodes.includes(e.target)))
    requireValue(graph.unresolved.every((u) => graph.nodes.includes(u.source_path)))
    if (graph.unresolved.length) requireValue(stages.graph.status === 'partial')
  }
  const evidence = stages.evidence.data?.items ?? []
  unique(evidence.map((e) => e.id))
  for (const e of evidence) {
    requireValue(knownSnapshot(e.snapshot))
    if ((e.resolution ?? 'unverified') !== 'unverified') requireValue(e.verification_reason != null)
    if ((e.support ?? 'unverified') !== 'unverified') requireValue(e.resolution === 'resolved')
  }
  if (evidence.some((e) => e.resolution !== 'resolved' || e.support !== 'supported')) requireValue(stages.evidence.status === 'partial')
  if (impact) {
    requireValue(graph && changes && same(impact.snapshot, graph.snapshot))
    unique(impact.paths.map((p) => p.id)); unique(impact.paths.map((p) => [p.changed_component_id, p.nodes]))
    unique(impact.candidates.map((c) => c.id)); unique(impact.candidates.map((c) => [c.path, c.symbol ?? null, c.changed_component_id]))
    const edges = new Set(graph.edges.map((e) => `${e.source}\0${e.target}`))
    const origin = (id: string) => {
      const component = changes.components.find((c) => c.id === id)
      requireValue(component)
      const base = same(graph.snapshot, identity.base)
      requireValue(base ? component.change !== 'added' : component.change !== 'deleted')
      return base ? component.previous_path ?? component.path : component.path
    }
    for (const p of impact.paths) {
      unique(p.nodes); requireValue(p.nodes.at(-1) === origin(p.changed_component_id))
      requireValue(p.nodes.slice(1).every((node, i) => edges.has(`${p.nodes[i]}\0${node}`)))
    }
    for (const c of impact.candidates) {
      const changed = origin(c.changed_component_id)
      unique(c.path_ids); unique(c.evidence_ids ?? [])
      requireValue(graph.nodes.includes(c.path) && (c.evidence_ids ?? []).every((id) => evidence.some((e) => e.id === id)))
      if (c.relationship === 'changed') requireValue(c.path === changed && c.path_ids.length === 0)
      else {
        requireValue(c.path_ids.length > 0)
        const paths = c.path_ids.map((id) => impact.paths.find((p) => p.id === id))
        requireValue(paths.every((p) => p && p.changed_component_id === c.changed_component_id && p.nodes[0] === c.path))
        const direct = edges.has(`${c.path}\0${changed}`)
        requireValue(c.relationship === (direct ? 'direct' : 'indirect'))
        if (direct) requireValue(paths.some((p) => p?.nodes.length === 2))
      }
    }
    if (stages.changes.status === 'partial' || stages.graph.status === 'partial') requireValue(stages.impact.status === 'partial')
  }
  if (stages.inventory.data) {
    const inventory = stages.inventory.data
    requireValue(knownSnapshot(inventory.snapshot) && same(inventory.snapshot, identity.target))
    unique(inventory.test_ids)
    if (inventory.completeness === 'partial') requireValue(stages.inventory.status === 'partial')
  }
  if (stages.retrieval.data) {
    const retrieval = stages.retrieval.data
    const sourceKey = (s: typeof retrieval.sources[number]) => [snapshotKey(s.snapshot), s.index_id, s.configuration_id]
    const keys = retrieval.sources.map((s) => JSON.stringify(sourceKey(s)))
    unique(keys); unique(retrieval.items.map((i) => i.id)); unique(retrieval.items.map((i) => i.rank))
    requireValue(retrieval.sources.every((s) => knownSnapshot(s.snapshot)))
    requireValue(retrieval.items.every((i) => keys.includes(JSON.stringify(sourceKey(i)))))
  }
  if (stages.review_ordering.data) {
    const review = stages.review_ordering.data
    requireValue(changes && graph && same(review.snapshot, graph.snapshot))
    unique(review.candidates.map((c) => [c.path, c.symbol ?? null]))
    requireValue(review.candidates.every((c) => graph.nodes.includes(c.path)))
    if (stages.changes.status === 'partial' || stages.graph.status === 'partial') requireValue(stages.review_ordering.status === 'partial')
  }
}
