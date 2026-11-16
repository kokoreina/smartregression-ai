import type { components } from '../../types/generated'
import { validateStageReport } from '../reports/stageReport'
import schema from '../../../../contracts/generated/openapi.json'

export type Overview = components['schemas']['RepositoryOverview']
export type Result = components['schemas']['RepositoryAnalysisResponse']

export const messages: Record<string, string> = {
  sensitive_question: 'Câu hỏi có dấu hiệu chứa credential. Hãy bỏ API key, mật khẩu hoặc token trước khi gửi Gemini.',
  repository_tree_incomplete: 'GitHub trả cây bị cắt bớt. Chưa thể hiển thị toàn bộ cấu trúc của commit này.',
  repository_tree_limit: 'Cây vượt giới hạn hiển thị: 5.000 mục hoặc 2 MB metadata. Hãy thử repo nhỏ hơn.',
  github_invalid_response: 'Metadata cây Git không hợp lệ. Hệ thống chưa hiển thị cây để tránh sai cấu trúc.',
  github_unavailable: 'Chưa kết nối được GitHub. Vui lòng thử lại sau.',
  github_redirect_rejected: 'Địa chỉ repo đã chuyển hướng. Hãy nhập URL GitHub chính thức hiện tại.',
  github_lookup_failed_or_rate_limited: 'Không đọc được repo. Kiểm tra URL public hoặc chờ GitHub hết giới hạn truy cập.',
  repository_limit: 'Repo vượt giới hạn bản thử: tối đa 1.000 file, 1 MB/file và 16 MB/snapshot; giới hạn tính cả video, ảnh và dữ liệu. Hãy chọn repo nhỏ hơn để thử.',
  github_rate_limit: 'GitHub đang giới hạn truy cập. Vui lòng thử lại sau.',
  github_timeout: 'GitHub phản hồi quá chậm. Vui lòng thử lại.',
  github_repository_or_commit_not_found: 'Không tìm thấy repo public hoặc commit đã chọn.',
  unsupported_snapshot_entry: 'Repo có submodule hoặc symlink; bản thử hiện chưa hỗ trợ.',
  snapshot_mismatch: 'Nội dung tải về không khớp snapshot Git; đã dừng phân tích.',
  snapshot_acquisition_failed: 'Không tải và xác minh được snapshot GitHub. Lượt này chưa tới bước gọi Gemini.',
  analysis_busy: 'Một lượt phân tích khác đang chạy. Vui lòng đợi hoàn tất.',
  provider_configuration: 'Backend chưa nạp cấu hình Gemini hợp lệ.',
  provider_timeout: 'Gemini hết thời gian phản hồi; kết quả phân tích tĩnh vẫn có bên dưới.',
  provider_budget: 'Đã chạm giới hạn context/ngân sách: tối đa 5 lượt Gemini cho phiên demo này.',
  provider_invalid_output: 'Gemini trả kết quả chưa qua kiểm tra định dạng hoặc tham chiếu; không hiển thị nhận định đó.',
  provider_quota: 'Tài khoản Gemini chưa đủ quota cho lượt này.',
  provider_auth: 'Backend không xác thực được với Gemini.',
}

export async function post(path: string, body: unknown, signal: AbortSignal): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal })
  } catch (error) {
    if (signal.aborted) throw error
    throw new Error('Không kết nối được API. Kiểm tra backend và thử lại; bạn vẫn có thể mở báo cáo đã lưu.')
  }
  let data: unknown
  try { data = await response.json() }
  catch { throw new Error('Backend chưa trả JSON hợp lệ. Kiểm tra kết nối API rồi thử lại.') }
  if (!response.ok) {
    const code = data && typeof data === 'object' && 'message' in data && typeof data.message === 'string'
      ? data.message : ''
    throw new Error(messages[code] ?? 'Không hoàn tất yêu cầu. Kiểm tra repo public, commit và kết nối backend.')
  }
  return data
}

function object(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}
const text = (value: unknown, max = 2000): value is string => typeof value === 'string' && value.length > 0 && value.length <= max
const optionalText = (value: unknown) => value == null || text(value)
const keys = (value: object, allowed: string[]) => Object.keys(value).every(k => allowed.includes(k))
const providerErrors: readonly string[] = schema.components.schemas.NarrativeResult.properties.error_code.anyOf.find(v => 'enum' in v)?.enum ?? []
function validUsage(value: unknown): boolean {
  if (value == null) return true
  return object(value) && keys(value, Object.keys(schema.components.schemas.ProviderUsage.properties))
    && Object.entries(value).every(([key, v]) => v == null || (typeof v === 'number' && Number.isFinite(v)
      && v >= 0 && (!key.endsWith('_tokens') || Number.isSafeInteger(v))))
}

export function overviewValue(value: unknown): Overview {
  if (!object(value) || !keys(value, ['schema_version', 'repository_url', 'full_name', 'default_branch', 'commits']) || !('schema_version' in value) || value.schema_version !== '1.0.0'
    || !('repository_url' in value) || typeof value.repository_url !== 'string'
    || !('full_name' in value) || typeof value.full_name !== 'string'
    || !('default_branch' in value) || typeof value.default_branch !== 'string'
    || !/^https:\/\/github\.com\/[A-Za-z0-9][A-Za-z0-9-]{0,38}\/[A-Za-z0-9_.-]{1,100}$/.test(value.repository_url)
    || value.repository_url.slice('https://github.com/'.length).toLowerCase() !== value.full_name.toLowerCase()
    || !('commits' in value) || !Array.isArray(value.commits) || value.commits.length > 10
    || !value.commits.every(c => c && typeof c === 'object' && typeof c.sha === 'string'
      && /^[a-f0-9]{40}$/.test(c.sha) && typeof c.message === 'string' && c.message.length <= 300
      && typeof c.date === 'string' && c.date.length <= 40 && keys(c, ['sha', 'message', 'date']))) {
    throw new Error('Backend trả thông tin repo không đúng định dạng.')
  }
  return value as Overview
}

export function analysisValue(value: unknown): Result {
  if (!object(value) || !keys(value, ['schema_version', 'repository', 'files', 'report', 'narrative', 'narrative_evidence', 'selection_status', 'execution_status', 'limitations']) || !('report' in value) || !('narrative' in value)
    || !('repository' in value) || !('files' in value) || !Array.isArray(value.files)
    || value.files.length > 1000 || !value.files.every(p => text(p)) || new Set(value.files).size !== value.files.length
    || !('limitations' in value) || !Array.isArray(value.limitations)
    || !value.limitations.every(p => typeof p === 'string')
    || !('selection_status' in value) || value.selection_status !== 'not_run'
    || !('execution_status' in value) || value.execution_status !== 'not_run') {
    throw new Error('Backend trả báo cáo không đúng định dạng.')
  }
  overviewValue(value.repository)
  validateStageReport(value.report)
  if (!('schema_version' in value) || value.schema_version !== '1.0.0'
    || !('narrative_evidence' in value) || !Array.isArray(value.narrative_evidence)
    || value.narrative_evidence.length > 180
    || !value.narrative_evidence.every(e => object(e)
      && text(e.id) && text(e.path) && keys(e, ['id', 'path', 'change', 'symbol', 'imports', 'relationship', 'explanation'])
      && ['change', 'symbol', 'imports', 'relationship', 'explanation'].every(k => optionalText(e[k])))) {
    throw new Error('Thiếu bằng chứng metadata cho nhận định Gemini.')
  }
  const evidence = new Map(value.narrative_evidence.map(e => [e.id, e.path]))
  if (evidence.size !== value.narrative_evidence.length) throw new Error('Tham chiếu metadata trùng lặp.')
  const narrative = value.narrative
  if (!object(narrative) || !('status' in narrative)
    || !keys(narrative, ['status', 'data', 'model', 'error_code', 'reason', 'usage', 'prompt_sha256'])
    || !['not_run', 'completed', 'failed'].includes(String(narrative.status))
    || !['model', 'reason', 'prompt_sha256'].every(k => optionalText(narrative[k]))
    || (narrative.status === 'completed' && narrative.error_code != null)
    || (narrative.status === 'completed' && narrative.reason != null)
    || (narrative.status === 'not_run' && narrative.error_code != null)
    || (narrative.status === 'failed' && narrative.reason != null)
    || (narrative.error_code != null && (typeof narrative.error_code !== 'string' || !providerErrors.includes(narrative.error_code)))
    || !validUsage(narrative.usage)
    || (narrative.status !== 'completed' && narrative.data != null)
    || (narrative.status === 'failed' && !text(narrative.error_code))) {
    throw new Error('Trạng thái Gemini không hợp lệ.')
  }
  if (narrative.status === 'completed') {
    if (!('data' in narrative) || !narrative.data || typeof narrative.data !== 'object') {
      throw new Error('Thiếu nội dung Gemini.')
    }
    const data = narrative.data
    if (!('summary' in data) || typeof data.summary !== 'string'
      || !text(data.summary) || !keys(data, ['summary', 'findings', 'limitations'])
      || !('findings' in data) || !Array.isArray(data.findings) || data.findings.length > 12
      || !data.findings.every(f => f && typeof f.path === 'string' && typeof f.explanation === 'string'
        && text(f.path) && text(f.explanation) && keys(f, ['path', 'explanation', 'evidence_ids'])
        && Array.isArray(f.evidence_ids) && f.evidence_ids.length > 0 && f.evidence_ids.length <= 8
        && new Set(f.evidence_ids).size === f.evidence_ids.length
        && f.evidence_ids.every((id: unknown) => typeof id === 'string' && evidence.get(id) === f.path))
      || !('limitations' in data) || !Array.isArray(data.limitations)
      || data.limitations.length > 8 || !data.limitations.every(l => text(l))) {
      throw new Error('Nội dung Gemini không đúng định dạng.')
    }
  }
  return value as Result
}

