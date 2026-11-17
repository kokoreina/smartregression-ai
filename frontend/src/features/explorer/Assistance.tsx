import { useEffect, useRef, useState } from 'react'
import type { components } from '../../types/generated'
import { productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'
import { SnapshotAi } from './SnapshotAi'

type Guide = components['schemas']['ReadingGuide']
type Search = components['schemas']['FeatureSearch']
type Evidence = components['schemas']['GraphEvidence']

export function Assistance({ base, path, choose }: { base: string; path: string; choose: (path: string, evidence: Evidence) => void }) {
  const [guide, setGuide] = useState<Guide | null>(null)
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<Search | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const flight = useRef(false)
  useEffect(() => {
    let active = true
    productRequest<Guide>(`${base}/reading-guide`).then(value => { if (active) setGuide(value) })
      .catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Chưa đọc được lộ trình.') })
    return () => { active = false }
  }, [base])
  async function search(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError('')
    try { setResult(await productRequest<Search>(`${base}/search`, 'POST', { query, top_k: 10 })) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Không tìm được chức năng.') }
    finally { flight.current = false; setBusy(false) }
  }
  const labels = { entrypoint: 'Điểm vào', module: 'Module', data: 'Dữ liệu', tests: 'Tests' }
  const segments = base.split('/')
  return <section className="assistance-panel"><h2>Hướng dẫn đọc và tìm chức năng</h2>
    <p>Dựa trên snapshot đã lưu. Các thao tác tại đây không gửi source hoặc gọi Gemini.</p>
    {error && <FormNotice error>{error}</FormNotice>}
    <details><summary>Lộ trình đọc tĩnh</summary>{guide && <>
      {guide.entrypoint_status === 'unknown' && <FormNotice>Chưa xác định điểm vào từ cấu hình được hỗ trợ.</FormNotice>}
      <ol>{guide.steps.map((step, index) => <li key={`${step.category}-${step.path}-${index}`}><strong>{labels[step.category]}</strong> · <button type="button" onClick={() => choose(step.evidence.path, step.evidence)}>{step.path}</button><p>{step.reason}</p><small>Bằng chứng: {step.evidence.path} · {guide.commit.slice(0, 12)}</small></li>)}</ol>
      <p>{guide.limitations.join(' ')}</p>
    </>}</details>
    <form onSubmit={search} aria-busy={busy}><label htmlFor="feature-query">Tìm chức năng trong snapshot</label><input id="feature-query" value={query} onChange={event => setQuery(event.target.value)} required maxLength={600} placeholder="Ví dụ: payment hoặc thanh toán" /><button disabled={busy} className="primary-button">{busy ? 'Đang tìm…' : 'Tìm bằng chứng'}</button></form>
    {result && <div aria-live="polite"><p>Truy vấn đã chạy: {result.query}</p>{result.status === 'no_evidence' ? <FormNotice>Không có bằng chứng khớp từ khóa trong phạm vi đã lập chỉ mục.</FormNotice> : <ol>{result.items.map(item => <li key={item.evidence.id}><button type="button" onClick={() => choose(item.path, item.evidence)}>{item.path}{item.symbol ? ` · ${item.symbol}` : ''}</button><p>Dòng {item.evidence.line_start}–{item.evidence.line_end} · từ khớp: {item.matched_terms.join(', ')}</p></li>)}</ol>}<p>{result.indexed_chunks} đoạn đã xét{result.truncated ? ' · đã giới hạn' : ''}. {result.limitations.join(' ')}</p></div>}
    <SnapshotAi key={`${base}-${path}`} projectId={segments[2] ?? ''} commit={segments[4] ?? ''} path={path || undefined} search={result?.query} choose={proof => choose(proof.path, { ...proof, kind: proof.line_start ? 'source_range' : 'metadata', line_start: proof.line_start ?? null, line_end: proof.line_end ?? null, source_kind: 'git', overlay_digest: null })} />
  </section>
}
