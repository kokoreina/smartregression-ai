import type { components } from '../../types/generated'

export type CurrentUser = components['schemas']['CurrentUser']
export type AuthMessage = components['schemas']['AuthMessage']
type Registration = components['schemas']['Registration']
type Login = components['schemas']['Login']
type PasswordReset = components['schemas']['PasswordReset']
type PasswordChange = components['schemas']['PasswordChange']
type ProfileUpdate = components['schemas']['ProfileUpdate']
type EmailInput = components['schemas']['EmailInput']

const messages: Record<string, string> = {
  invalid_credentials: 'Email hoặc mật khẩu chưa đúng.',
  authentication_required: 'Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.',
  email_verification_required: 'Hãy xác thực email để tiếp tục.',
  csrf_invalid: 'Biểu mẫu đã hết hạn. Hãy bấm gửi lại; thông tin chưa được gửi lại tự động.',
  invalid_origin: 'Địa chỉ mở ứng dụng không khớp cấu hình server.',
  invalid_host: 'Địa chỉ ứng dụng chưa được cho phép.',
  invalid_request: 'Thông tin chưa hợp lệ. Hãy kiểm tra lại các trường trong biểu mẫu.',
  invalid_or_expired_token: 'Liên kết đã hết hạn hoặc được sử dụng. Hãy yêu cầu email mới.',
  rate_limited: 'Bạn đã thử quá nhiều lần. Vui lòng đợi trước khi thử lại.',
  authentication_unavailable: 'Dịch vụ tài khoản chưa được cấu hình hoặc đang tạm ngừng.',
  account_storage_unavailable: 'Chưa kết nối được dữ liệu tài khoản. Vui lòng thử lại sau.',
  ai_quota_exhausted: 'Tài khoản chưa có quota AI hoặc đã dùng hết ngân sách được cấp.',
  ai_busy: 'Một yêu cầu AI đang được xử lý. Vui lòng đợi, không gửi lặp.',
  analysis_busy: 'Đã có phân tích đang chạy hoặc hệ thống đủ số lượt đồng thời. Vui lòng đợi.',
  project_archived: 'Dự án đã lưu trữ. Hãy khôi phục trước khi tạo phân tích mới.',
  idempotency_conflict: 'Mã yêu cầu đã dùng cho nội dung khác. Hãy kiểm tra lại lựa chọn.',
  github_rate_limit: 'GitHub đang giới hạn truy cập. Hãy đợi trước khi thử lại; báo cáo đã lưu vẫn mở được.',
  github_timeout: 'GitHub phản hồi quá chậm. Hãy thử lại sau hoặc mở báo cáo đã lưu.',
  github_unavailable: 'Chưa kết nối được GitHub. Kiểm tra mạng rồi thử lại sau.',
  github_repository_or_commit_not_found: 'Không tìm thấy repo public hoặc commit. Kiểm tra URL và SHA đầy đủ.',
  repository_lookup_failed: 'Không đọc được repo public. Kiểm tra URL, kết nối hoặc thử lại sau.',
  repository_limit: 'Repo vượt giới hạn 1.000 file, 16 MB/snapshot hoặc 1 MB/file. Hãy chọn repo nhỏ hơn.',
  repository_tree_limit: 'Cây vượt giới hạn 5.000 mục. Hãy chọn repo nhỏ hơn.',
  repository_tree_incomplete: 'GitHub trả cây chưa đầy đủ. Chưa thể dùng snapshot này.',
  snapshot_not_ready: 'Snapshot chưa được lưu. Hãy bấm Tải snapshot và graph trước.',
  snapshot_mismatch: 'Dữ liệu không khớp commit. Kiểm tra SHA và tải lại snapshot.',
  explorer_snapshot_failed: 'Chưa tạo được snapshot. Kiểm tra repo, SHA và giới hạn hỗ trợ.',
  version_conflict: 'Dữ liệu đã được cập nhật ở phiên khác. Tải lại trước khi lưu.',
  active_project_limit: 'Tài khoản đã có 3 dự án hoạt động. Lưu trữ một dự án trước khi tạo thêm.',
  source_not_available: 'File hoặc thư mục không có trong phạm vi source được phép xem ở snapshot này.',
  source_range_limit: 'Đoạn source vượt giới hạn 200 dòng hoặc 20 KB. Hãy thu hẹp phạm vi.',
  excerpt_scope_mismatch: 'Excerpt chưa thuộc phạm vi giải thích đã chọn. Xem lại file và loại yêu cầu.',
  excerpt_limit: 'Tổng excerpt vượt 20 KiB. Hãy chọn ít nội dung hơn.',
  ai_context_limit: 'Context vượt ngân sách gửi AI. Hãy chọn file hoặc phạm vi nhỏ hơn.',
  no_evidence: 'Chưa có bằng chứng phù hợp. Hãy đổi từ khóa hoặc chọn snapshot/file khác.',
  assistant_unavailable: 'Trợ lý chưa sẵn sàng. Hãy kiểm tra backend và migration dữ liệu.',
  thread_not_found: 'Hội thoại không còn tồn tại hoặc bạn không có quyền truy cập.',
  thread_config_mismatch: 'Hội thoại dùng phiên bản phân tích cũ. Hãy tạo hội thoại mới cho snapshot này.',
  thread_limit: 'Dự án đã có 100 hội thoại. Hãy xóa hội thoại không cần giữ trước khi tạo thêm.',
  message_limit: 'Hội thoại đã đủ 100 lượt. Hãy tạo hội thoại mới để tiếp tục.',
  unknown_watch_path: 'Có đường dẫn theo dõi không tồn tại ở nhánh đã chọn. Hãy kiểm tra cây thư mục.',
  watch_not_configured: 'Hãy lưu nhánh và vùng mã theo dõi trước khi kiểm tra thay đổi.',
  change_report_not_available: 'Chưa có báo cáo thay đổi cho commit này. Hãy đồng bộ nhánh rồi mở thông báo tương ứng.',
  invalid_search_query: 'Truy vấn cần 1–600 ký tự và tối đa 10 kết quả.',
  sensitive_question: 'Nội dung có dấu hiệu thông tin nhạy cảm. Hãy loại bỏ trước khi gửi.',
  sensitive_input: 'Nội dung có dấu hiệu thông tin nhạy cảm. Hãy loại bỏ trước khi lưu phương án.',
  report_view_not_found: 'Snapshot dashboard không còn khả dụng hoặc đã hết hạn. Hãy cập nhật tổng quan.',
  export_row_limit: 'Bộ lọc vượt 10.000 dòng. Hãy thu hẹp dự án hoặc khoảng thời gian.',
  invalid_report_filter: 'Bộ lọc thời gian chưa hợp lệ. Hãy chọn khoảng trong quá khứ và múi giờ hợp lệ.',
}

export class AccountError extends Error {
  constructor(public code: string, public status: number, public retryAfter?: number) {
    super(messages[code] ?? 'Không thể hoàn tất yêu cầu. Hãy thử lại sau.')
  }
}

let csrf: string | null = null
let csrfRequest: Promise<string> | null = null
let generation = 0
export function clearAuthClient() { ++generation; csrf = null; csrfRequest = null }

async function token(): Promise<string> {
  if (csrf) return csrf
  if (!csrfRequest) {
    csrfRequest = fetch('/api/v1/auth/csrf', { credentials: 'same-origin', cache: 'no-store', signal: AbortSignal.timeout(5000) })
      .then(async response => {
        if (!response.ok) throw new AccountError('authentication_unavailable', response.status)
        const data: unknown = await response.json()
        if (typeof data !== 'object' || data === null || !('token' in data) || typeof data.token !== 'string') {
          throw new AccountError('authentication_unavailable', 503)
        }
        csrf = data.token
        return csrf
      }).finally(() => { csrfRequest = null })
  }
  return csrfRequest
}

function unauthenticated() { window.dispatchEvent(new Event('sr:session-expired')) }

async function request<T>(path: string, method = 'GET', body?: unknown, kind: 'json' | 'blob' = 'json'): Promise<T> {
  const started = generation
  try {
    const headers: Record<string, string> = {}
    const acquiresSnapshot = (method === 'POST' && (path === '/projects' || path.endsWith('/snapshots') || path.endsWith('/assistant/overview') || path.endsWith('/assistant/threads')))
      || (method === 'PUT' && path.endsWith('/assistant/watch'))
    if (method !== 'GET') {
      headers['Content-Type'] = 'application/json'
      headers['X-CSRF-Token'] = await token()
    }
    const response = await fetch(path.startsWith('/') ? `/api/v1${path}` : `/api/v1/auth/${path}`, {
      method, credentials: 'same-origin', cache: 'no-store', headers, signal: AbortSignal.timeout(acquiresSnapshot ? 180000 : 30000),
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
    if (response.ok && kind === 'blob') return await response.blob() as T
    if (response.status === 204) return undefined as T
    const data: unknown = await response.json()
    if (!response.ok) {
      const code = typeof data === 'object' && data !== null && 'code' in data && typeof data.code === 'string'
        ? data.code : 'request_failed'
      if (response.status === 401 && code !== 'invalid_credentials' && path !== 'login' && started === generation) { clearAuthClient(); unauthenticated() }
      if (code === 'csrf_invalid') {
        clearAuthClient()
        // Refresh only CSRF. A failed mutation is never replayed automatically.
        await token().catch(() => undefined)
      }
      const retry = Number(response.headers.get('retry-after'))
      throw new AccountError(code, response.status, retry > 0 ? retry : undefined)
    }
    if (['login', 'logout', 'reset-password', 'change-password'].includes(path)) clearAuthClient()
    return data as T
  } catch (error) {
    if (error instanceof AccountError) throw error
    throw new Error('Không kết nối được API. Kiểm tra mạng hoặc thử lại sau.')
  }
}

export const accountApi = {
  me: () => request<CurrentUser>('me'),
  login: (body: Login) => request<CurrentUser>('login', 'POST', body),
  register: (body: Registration) => request<AuthMessage>('register', 'POST', body),
  logout: () => request<AuthMessage>('logout', 'POST', {}),
  profile: (body: ProfileUpdate) => request<CurrentUser>('me', 'PATCH', body),
  resend: (body: EmailInput) => request<AuthMessage>('resend-verification', 'POST', body),
  forgot: (body: EmailInput) => request<AuthMessage>('forgot-password', 'POST', body),
  verify: (value: string) => request<AuthMessage>('verify-email', 'POST', { token: value }),
  reset: (body: PasswordReset) => request<AuthMessage>('reset-password', 'POST', body),
  change: (body: PasswordChange) => request<AuthMessage>('change-password', 'POST', body),
}

// Product data shares cookie/CSRF handling and session-expiry invalidation.
export function productRequest<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  return request<T>(path, method, body)
}

export function productDownload(path: string): Promise<Blob> { return request<Blob>(path, 'POST', {}, 'blob') }
