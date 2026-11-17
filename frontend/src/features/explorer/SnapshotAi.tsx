import { useEffect, useRef, useState } from 'react'
import type { components } from '../../types/generated'
import { productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'

type Job = components['schemas']['AiJob']
type Request = components['schemas']['AssistanceAiRequest']
type Source = components['schemas']['SourceRange']
type Proof = { id: string; path: string; commit: string; line_start?: number | null; line_end?: number | null }

export function SnapshotAi({ projectId, commit, path, search, scenarioId, choose }: {
  projectId: string; commit: string; path?: string; search?: string; scenarioId?: string;
  choose?: (proof: Proof) => void;
}) {
  const [action, setAction] = useState<Request['action']>(scenarioId ? 'hypothesis' : path ? 'file' : 'reading_guide')
  const [question, setQuestion] = useState(search ?? '')
  const [consent, setConsent] = useState(false)
  const [excerptConsent, setExcerptConsent] = useState(false)
  const [start, setStart] = useState(1)
  const [end, setEnd] = useState(40)
  const [preview, setPreview] = useState<Source | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const flight = useRef(false)
  const retry = useRef<{ signature: string; key: string } | null>(null)
  const base = `/projects/${projectId}/assistance/ai`
  useEffect(() => {
    let active = true
    let timer: ReturnType<typeof setTimeout> | undefined
    async function load() {
      try {
        const result = await productRequest<Job[]>(`${base}?commit=${commit}`)
        if (!active) return
        setJobs(result)
        if (result.some(job => job.status === 'queued' || job.status === 'running')) timer = setTimeout(() => { void load() }, 1500)
      } catch (cause) { if (active) setError(cause instanceof Error ? cause.message : 'Chưa đọc được AI đã lưu.') }
    }
    void load()
    return () => { active = false; clearTimeout(timer) }
  }, [base, commit, busy])
  async function previewSource() {
    if (!path) return
    setError(''); setExcerptConsent(false); setPreview(null)
    try { setPreview(await productRequest<Source>(`/projects/${projectId}/snapshots/${commit}/source?path=${encodeURIComponent(path)}&start=${start}&end=${end}`)) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Không mở được excerpt.') }
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError('')
    const input = { commit, action, question: action === 'search' ? (search || question) : question,
      path: path || null, scenario_id: scenarioId || null, allow_metadata_egress: consent,
      allow_excerpt_egress: excerptConsent,
      excerpts: preview && excerptConsent ? [{ path: preview.path, start: preview.line_start, end: preview.line_end }] : [] }
    const signature = JSON.stringify(input)
    if (retry.current?.signature !== signature) retry.current = { signature, key: crypto.randomUUID() }
    try { const job = await productRequest<Job>(base, 'POST', { ...input, idempotency_key: retry.current.key }); setJobs(previous => [job, ...previous.filter(item => item.id !== job.id)]) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Không tạo được yêu cầu AI. Kết quả tĩnh vẫn được giữ.') }
    finally { flight.current = false; setBusy(false) }
  }
  function proofs(job: Job): Proof[] {
    const values = job.provenance?.observations
    return Array.isArray(values) ? values.filter((item): item is Proof => !!item && typeof item === 'object' && typeof item.id === 'string' && typeof item.path === 'string' && item.commit === commit) : []
  }
  return <details className="snapshot-ai"><summary>Gemini — giải thích có bằng chứng</summary><p>Mở kết quả đã lưu không gọi provider. Mỗi yêu cầu mới cần consent và quota được operator cấp.</p>
    {error && <FormNotice error>{error}</FormNotice>}
    <form onSubmit={submit} aria-busy={busy}><label htmlFor="assist-action">Loại giải thích</label><select id="assist-action" value={action} onChange={event => setAction(event.target.value as Request['action'])} disabled={busy}>
      <option value="reading_guide">Lộ trình đọc</option><option value="search">Tìm chức năng</option>{path && <><option value="file">File</option><option value="folder">Thư mục</option></>}{scenarioId && <option value="hypothesis">Giả thuyết thay đổi</option>}</select>
      <label htmlFor="assist-question">Câu hỏi hoặc từ khóa</label><textarea id="assist-question" value={question} onChange={event => setQuestion(event.target.value)} maxLength={600} disabled={busy} />
      <label className="checkbox-label"><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} disabled={busy} />Tôi đồng ý gửi metadata: đường dẫn, symbols, quan hệ, bằng chứng và câu hỏi tới Gemini.</label>
      {path && <details><summary>Chọn excerpt nguồn — tùy chọn</summary><p>Chỉ đoạn đang xem dưới đây được gửi khi bạn đồng ý riêng. Không gửi toàn bộ repo.</p><div className="dialog-actions"><label>Từ dòng<input type="number" min={1} value={start} onChange={event => { setStart(Number(event.target.value)); setPreview(null); setExcerptConsent(false) }} /></label><label>Đến dòng<input type="number" min={1} value={end} onChange={event => { setEnd(Number(event.target.value)); setPreview(null); setExcerptConsent(false) }} /></label></div><button type="button" onClick={() => void previewSource()}>Xem trước excerpt</button>
        {preview && <><p>{preview.path} · {preview.commit} · dòng {preview.line_start}–{preview.line_end}</p><pre className="source-range"><code>{preview.content}</code></pre><label className="checkbox-label"><input type="checkbox" checked={excerptConsent} onChange={event => setExcerptConsent(event.target.checked)} />Tôi đồng ý gửi đúng đoạn source đã xem trước này.</label></>}
      </details>}
      <button className="primary-button" disabled={busy || !consent}>{busy ? 'Đang gửi yêu cầu…' : 'Yêu cầu Gemini'}</button><p className="field-hint">Đóng trang chỉ dừng theo dõi; không xác nhận provider đã hủy hoặc được hoàn tiền.</p>
    </form>
    <h3>Giải thích đã lưu của snapshot</h3>{jobs.length === 0 && <p>Chưa có yêu cầu AI.</p>}{jobs.map(job => <article className="saved-explanation" key={job.id}><h4>{job.action} · {new Date(job.created_at).toLocaleString()}</h4><p>{job.status} · {job.result?.model ?? 'Chưa có thông tin model'}</p>
      {job.result?.status === 'failed' && <FormNotice error>Gemini chưa hoàn tất: {job.result.error_code}. Phần tĩnh vẫn sử dụng được.</FormNotice>}
      {job.result?.data && <><p>{job.result.data.summary}</p>{job.result.data.findings.map((finding, index) => <div key={index}><p><strong>{finding.path}</strong> — {finding.explanation}</p>{finding.evidence_ids.map(id => { const proof = proofs(job).find(item => item.id === id); return proof && choose ? <button type="button" key={id} onClick={() => choose(proof)}>Bằng chứng {id.slice(0, 10)}</button> : <code key={id}>{id}</code> })}</div>)}<p>{job.result.data.limitations.join(' ')}</p></>}
      <small>Context hash: {job.context_hash ?? 'Không có thông tin'}. Chi phí chưa biết không được xem là 0.</small>
    </article>)}
  </details>
}
