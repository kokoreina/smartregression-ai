import type { components } from '../../types/generated'
import { analysisValue, type Result } from './repositoryClient'

type Export = components['schemas']['RepositoryReportExport']
export type LoadedRepositoryReport = { result: Result; exportedAt: string | null }

function exportTime(value: unknown): asserts value is string {
  if (typeof value !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(value)
    || !Number.isFinite(Date.parse(value))) throw new Error('Thời điểm xuất báo cáo không hợp lệ hoặc thiếu múi giờ.')
  const day = new Date(`${value.slice(0, 10)}T00:00:00Z`)
  if (day.toISOString().slice(0, 10) !== value.slice(0, 10)) throw new Error('Ngày xuất báo cáo không hợp lệ.')
}

export function exportReport(result: Result, exportedAt = new Date().toISOString()): Export {
  exportTime(exportedAt)
  return { report_kind: 'repository-analysis', schema_version: '1.0.0', exported_at: exportedAt, payload: analysisValue(result) }
}

async function reportIdentity(value: unknown): Promise<Result> {
  const result = analysisValue(value)
  if (result.report.data_kind === 'real') {
    const bytes = new TextEncoder().encode(result.repository.full_name.toLowerCase())
    const digest = await crypto.subtle.digest('SHA-256', bytes)
    const expected = 'github-' + Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('')
    if (result.report.identity.repository_id !== expected) throw new Error('Báo cáo không khớp định danh repository.')
  }
  return result
}

export async function loadRepositoryReport(file: File): Promise<LoadedRepositoryReport> {
  if (file.size > 16 * 1024 * 1024) throw new Error('Báo cáo vượt giới hạn 16 MiB.')
  let value: unknown
  try { value = JSON.parse(await file.text()) }
  catch { throw new Error('Không đọc được file JSON hợp lệ.') }
  if (value && typeof value === 'object' && 'report_kind' in value) {
    if (value.report_kind === 'saved-web-run') {
      if (!('schema_version' in value) || value.schema_version !== '1.0.0' || !('exported_at' in value) || !('payload' in value)
        || typeof value.payload !== 'object' || value.payload === null || !('payload' in value.payload) || !('run' in value.payload)) throw new Error('Báo cáo web không hợp lệ.')
      exportTime(value.exported_at)
      const result = await reportIdentity(value.payload.payload)
      const run = value.payload.run
      if (typeof run !== 'object' || run === null || !('base' in run) || run.base !== result.report.identity.base.commit || !('target' in run) || run.target !== result.report.identity.target.commit
        || !('repository_url' in run) || run.repository_url !== result.repository.repository_url) throw new Error('Định danh run không khớp báo cáo.')
      return { result, exportedAt: value.exported_at }
    }
    if (value.report_kind !== 'repository-analysis' || !('schema_version' in value) || value.schema_version !== '1.0.0'
      || !('payload' in value) || !('exported_at' in value)
      || Object.keys(value).some(k => !['report_kind', 'schema_version', 'exported_at', 'payload'].includes(k))) {
      throw new Error('Định dạng hoặc phiên bản báo cáo chưa được hỗ trợ.')
    }
    exportTime(value.exported_at)
    return { result: await reportIdentity(value.payload), exportedAt: value.exported_at }
  }
  return { result: await reportIdentity(value), exportedAt: null }
}
