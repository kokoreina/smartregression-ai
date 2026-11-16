import { useEffect, useRef, useState } from 'react'
import type { components } from '../../types/generated'
import { productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'

type Quota = components['schemas']['AiQuota']
type Job = components['schemas']['AiJob']
type Narrative = components['schemas']['NarrativeResult']

export function RunAi({ projectId, runId, onResult }: { projectId: string; runId: string; onResult: (result: Narrative) => void }) {
  const [quota, setQuota] = useState<Quota | null>(null)
  const [question, setQuestion] = useState('Giải thích ảnh hưởng từ bằng chứng phân tích.')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const flight = useRef(false)
  const active = useRef(true)
  const attempt = useRef<{ question: string; key: string } | null>(null)
  useEffect(() => {
    active.current = true
    productRequest<Quota>('/usage').then(value => { if (active.current) setQuota(value) }).catch(() => { if (active.current) setNotice('Thông tin quota AI chưa sẵn sàng; báo cáo tĩnh vẫn sử dụng được.') })
    return () => { active.current = false }
  }, [])

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current || !consent) return
    flight.current = true; setBusy(true); setError(''); setNotice('')
    if (!attempt.current || attempt.current.question !== question) attempt.current = { question, key: crypto.randomUUID() }
    try {
      let job = await productRequest<Job>(`/projects/${projectId}/runs/${runId}/ai`, 'POST', { question, allow_metadata_egress: consent, idempotency_key: attempt.current.key })
      for (let index = 0; ['queued', 'running'].includes(job.status) && index < 35 && active.current; index++) {
        await new Promise(resolve => window.setTimeout(resolve, 1000))
        if (!active.current) return
        job = await productRequest<Job>(`/projects/${projectId}/runs/${runId}/ai/${job.id}`)
      }
      if (!active.current) return
      if (job.result) { onResult(job.result); setNotice(job.status === 'completed' ? 'Giải thích đã được lưu. Mở lại báo cáo không gọi Gemini nữa.' : 'AI chưa hoàn tất; phần phân tích tĩnh vẫn được giữ. Không tự gửi lại yêu cầu.') }
      else setNotice('Yêu cầu vẫn đang xử lý. Mở lại báo cáo sau; hệ thống không tự tạo lượt mới.')
      setQuota(await productRequest<Quota>('/usage'))
    } catch (cause) { if (active.current) setError(cause instanceof Error ? cause.message : 'Không hoàn tất yêu cầu AI.') }
    finally { flight.current = false; if (active.current) setBusy(false) }
  }

  return <form className="auth-card project-create" onSubmit={submit} aria-busy={busy}><h2>Gemini hỗ trợ phân tích</h2>
    <p>Chỉ gửi metadata: repo, SHA, đường dẫn, quan hệ phụ thuộc, thay đổi và câu hỏi. Không gửi toàn bộ source code.</p>
    {quota && <p>Đã dùng {quota.used_calls}/{quota.granted_calls} lượt được cấp. Ngân sách tối đa {(quota.cap_micro_usd / 1_000_000).toFixed(2)} USD; {quota.unknown_actual_count} lượt chưa xác định chi phí thực.</p>}
    <label htmlFor="ai-question">Câu hỏi cho Gemini</label><textarea id="ai-question" value={question} maxLength={600} disabled={busy} onChange={e => { setQuestion(e.target.value); attempt.current = null }} />
    <label className="checkbox-label"><input type="checkbox" checked={consent} disabled={busy} onChange={e => setConsent(e.target.checked)} />Tôi đồng ý gửi metadata và câu hỏi tới Gemini.</label>
    <p className="field-hint">Không nhập mật khẩu, API key hoặc source nhạy cảm vào câu hỏi. Quota do operator cấp; tài khoản mới mặc định bằng 0.</p>
    {error && <FormNotice error>{error}</FormNotice>}{notice && <FormNotice>{notice}</FormNotice>}
    <button className="primary-button" disabled={busy || !consent || !quota || quota.used_calls >= quota.granted_calls}>{busy ? 'Đang chờ Gemini…' : 'Yêu cầu giải thích và lưu'}</button>
  </form>
}
