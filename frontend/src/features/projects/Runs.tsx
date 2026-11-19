import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import type { components } from '../../types/generated'
import { productRequest, productDownload } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'
import { RepositoryResult } from '../repositories/RepositoryAnalysis'
import { analysisValue } from '../repositories/repositoryClient'
import { RunAi } from './RunAi'

type Run = components['schemas']['WebRun']
type Page = components['schemas']['RunPage']
type Saved = components['schemas']['SavedRunReport']
type Overview = components['schemas']['RepositoryOverview']
const states: Record<string, string> = { queued: 'Đang chờ', running: 'Đang phân tích', completed: 'Đã kết thúc phân tích', failed: 'Phân tích lỗi', interrupted: 'Bị gián đoạn' }

async function download(saved: Saved) {
  const blob = await productDownload(`/projects/${saved.run.project_id}/runs/${saved.run.id}/export`)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a'); link.href = url; link.download = `smartregression-${saved.run.id}.json`; link.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function ProjectRuns({ projectId, archived }: { projectId: string; archived: boolean }) {
  const [params, setParams] = useSearchParams()
  const value = params.get('runStatus') ?? ''
  const status = Object.hasOwn(states, value) ? value : ''
  return <><label htmlFor="history-status">Lọc trạng thái lịch sử</label>
    <select id="history-status" value={status} onChange={event => setParams(previous => {
      const next = new URLSearchParams(previous)
      if (event.target.value) next.set('runStatus', event.target.value)
      else next.delete('runStatus')
      return next
    })}><option value="">Tất cả trạng thái</option>{Object.entries(states).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>
    <ProjectRunsContent key={`${projectId}:${status}`} projectId={projectId} archived={archived} status={status} /></>
}

function ProjectRunsContent({ projectId, archived, status }: { projectId: string; archived: boolean; status: string }) {
  const [runs, setRuns] = useState<Run[]>([])
  const [base, setBase] = useState('')
  const [target, setTarget] = useState('')
  const [overview, setOverview] = useState<Overview | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [cursor, setCursor] = useState<string | null>(null)
  const initialized = useRef(false)
  const inFlight = useRef(false)
  const request = useRef<{ key: string; base: string; target: string } | null>(null)
  useEffect(() => {
    let cancelled = false
    let refreshing = false
    async function refresh() {
      if (refreshing) return
      refreshing = true
      try {
        const result = await productRequest<Page>(`/projects/${projectId}/runs${status ? `?status=${encodeURIComponent(status)}` : ''}`)
        if (!cancelled) {
          setRuns(old => ['queued', 'running'].includes(status) ? result.items : [...result.items, ...old.filter(run => !result.items.some(item => item.id === run.id))])
          if (!initialized.current) { setCursor(result.next_cursor ?? null); initialized.current = true }
        }
      } catch (cause) { if (!cancelled) setError(cause instanceof Error ? cause.message : 'Không tải được lịch sử.') }
      finally { refreshing = false }
    }
    void refresh()
    const timer = window.setInterval(() => void refresh(), 4000)
    return () => { cancelled = true; window.clearInterval(timer) }
  }, [projectId, status])

  async function inspect() {
    if (inFlight.current) return
    inFlight.current = true; setBusy(true); setError('')
    try {
      const data = await productRequest<Overview>(`/projects/${projectId}/repository`)
      setOverview(data); setTarget(data.commits[0]?.sha ?? ''); setBase(data.commits[1]?.sha ?? data.commits[0]?.sha ?? '')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Không đọc được GitHub.') }
    finally { inFlight.current = false; setBusy(false) }
  }

  async function more() {
    if (!cursor || inFlight.current) return
    inFlight.current = true; setBusy(true); setError('')
    try {
      const page = await productRequest<Page>(`/projects/${projectId}/runs?cursor=${encodeURIComponent(cursor)}${status ? `&status=${encodeURIComponent(status)}` : ''}`)
      setRuns(old => [...old, ...page.items.filter(item => !old.some(run => run.id === item.id))]); setCursor(page.next_cursor ?? null)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa tải được trang lịch sử.') }
    finally { inFlight.current = false; setBusy(false) }
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (inFlight.current) return
    inFlight.current = true; setBusy(true); setError(''); setNotice('')
    if (!request.current || request.current.base !== base || request.current.target !== target) request.current = { key: crypto.randomUUID(), base, target }
    try {
      const result = await productRequest<Run>(`/projects/${projectId}/runs`, 'POST', { base, target, idempotency_key: request.current.key })
      if (!status || result.status === status) setRuns(old => [result, ...old.filter(run => run.id !== result.id)])
      setNotice('Yêu cầu đã được lưu. Phân tích tĩnh không gọi Gemini hoặc chạy test.')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa tạo được phân tích.') }
    finally { inFlight.current = false; setBusy(false) }
  }

  return <section className="auth-card activity-card"><div className="page-title-row"><h2>Phân tích và lịch sử</h2><button type="button" disabled={busy} onClick={() => void inspect()}>Đọc commit GitHub</button></div>
    {error && <FormNotice error>{error}</FormNotice>}{notice && <FormNotice>{notice}</FormNotice>}
    {archived ? <p>Dự án đã lưu trữ: bạn vẫn có thể mở báo cáo cũ.</p> : <form className="project-create" onSubmit={submit} aria-busy={busy}>
      <label htmlFor="run-base">Base SHA</label><input id="run-base" list="project-commits" value={base} onChange={e => { setBase(e.target.value); request.current = null }} pattern="[0-9a-f]{40}" required minLength={40} maxLength={40} disabled={busy} />
      <label htmlFor="run-target">Target SHA</label><input id="run-target" list="project-commits" value={target} onChange={e => { setTarget(e.target.value); request.current = null }} pattern="[0-9a-f]{40}" required minLength={40} maxLength={40} disabled={busy} />
      <datalist id="project-commits">{overview?.commits.map(commit => <option value={commit.sha} key={commit.sha}>{commit.message}</option>)}</datalist>
      <p className="field-hint">Kết quả lưu với SHA đầy đủ. Hiện hỗ trợ phân tích tĩnh Python; chưa chạy regression test.</p>
      <button className="primary-button" disabled={busy}>{busy ? 'Đang tiếp nhận…' : 'Phân tích tĩnh và lưu kết quả'}</button>
    </form>}
    {runs.length === 0 ? <p>Chưa có phân tích được lưu.</p> : <ul>{runs.map(run => <li key={run.id}><div><Link to={`/app/projects/${projectId}/runs/${run.id}`}>{states[run.status]}</Link><p className="repository-url">{run.base.slice(0, 8)} → {run.target.slice(0, 8)}</p></div><time dateTime={run.started_at}>{new Date(run.started_at).toLocaleString('vi-VN')}</time></li>)}</ul>}{cursor && <button disabled={busy} onClick={() => void more()}>Tải thêm lịch sử</button>}
  </section>
}

export function RunDetail() {
  const { projectId, runId } = useParams()
  const [run, setRun] = useState<Run | null>(null)
  const [saved, setSaved] = useState<Saved | null>(null)
  const [error, setError] = useState('')
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    let cancelled = false
    let timer: number | undefined
    async function read() {
      try {
        const value = await productRequest<Run>(`/projects/${projectId}/runs/${runId}`)
        if (cancelled) return
        setRun(value)
        if (value.report_available) {
          const report = await productRequest<Saved>(`/projects/${projectId}/runs/${runId}/report`)
          analysisValue(report.payload)
          if (!cancelled) setSaved(report)
        }
        if (['queued', 'running'].includes(value.status) && !cancelled) timer = window.setTimeout(() => void read(), 2000)
      } catch (cause) { if (!cancelled) setError(cause instanceof Error ? cause.message : 'Không mở được báo cáo.') }
    }
    void read()
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [projectId, runId])
  return <section><Link to={`/app/projects/${projectId}`}>← Về dự án</Link><h1>Chi tiết phân tích</h1>
    {error && <FormNotice error>{error}</FormNotice>}
    {!run || run.id !== runId ? !error && <p role="status">Đang đọc kết quả đã lưu…</p> : <><p role="status">{states[run.status]}</p><p className="repository-url">{run.base} → {run.target}</p>
      <Link className="text-link" to={`/app/projects/${projectId}/explorer?commit=${run.target}`}>Khám phá graph tại target SHA →</Link>
      {run.error_code && <FormNotice error>Phân tích chưa hoàn tất: {run.error_code}. Hệ thống không tự gọi lại.</FormNotice>}
      {saved?.run.id === runId && <><RunAi key={runId} projectId={saved.run.project_id} runId={saved.run.id} onResult={narrative => setSaved(current => current ? { ...current, payload: { ...current.payload, narrative } } : null)} />
        <RepositoryResult result={analysisValue(saved.payload)} headingRef={heading} saved onDownload={() => { void download(saved).catch(cause => setError(cause instanceof Error ? cause.message : 'Không xuất được báo cáo.')) }} /></>}
    </>}
  </section>
}
