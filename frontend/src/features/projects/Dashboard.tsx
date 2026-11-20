import { useEffect, useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import { Link, useSearchParams } from 'react-router-dom'
import type { components } from '../../types/generated'
import { productDownload, productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'
import { WorkspaceIcon } from '../../components/WorkspaceIcon'
import { DashboardCharts } from './DashboardCharts'
import './dashboard.css'

type Summary = components['schemas']['Dashboard']
type Page = components['schemas']['RunPage']
type Projects = components['schemas']['ProjectPage']
type Usage = components['schemas']['UsagePage']

function RunTable({ items }: { items: Page['items'] }) {
  return <div className="table-scroll"><table><thead><tr><th>Run</th><th>Commit</th><th>Tĩnh / AI</th><th>Bắt đầu</th></tr></thead><tbody>{items.map(run => <tr key={run.id}><td><Link to={`/app/projects/${run.project_id}/runs/${run.id}`}>{run.id.slice(0, 12)}</Link></td><td>{run.base.slice(0, 8)} → {run.target.slice(0, 8)}</td><td>{run.status} / {run.ai_status}</td><td>{new Date(run.started_at).toLocaleString()}</td></tr>)}</tbody></table></div>
}

function UsageTable({ items }: { items: Usage['items'] }) {
  if (!items.length) return <p>Chưa có yêu cầu AI trong bộ lọc.</p>
  return <div className="table-scroll"><table><thead><tr><th>Yêu cầu</th><th>Loại / trạng thái</th><th>Chi phí đã biết</th><th>Giữ chỗ chưa quyết toán</th></tr></thead><tbody>{items.map(item => <tr key={item.id}><td>{item.id.slice(0, 12)}</td><td>{item.action} / {item.status}</td><td>{item.actual_micro_usd == null ? 'Chưa biết' : `${(item.actual_micro_usd / 1e6).toFixed(6)} USD`}</td><td>{item.actual_micro_usd == null ? `${(item.reservation_micro_usd / 1e6).toFixed(6)} USD` : 'Đã quyết toán'}</td></tr>)}</tbody></table></div>
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function Dashboard() {
  const [params, setParams] = useSearchParams()
  const viewId = params.get('view') ?? ''
  const [summary, setSummary] = useState<Summary | null>(null)
  const [rows, setRows] = useState<Page | null>(null)
  const [projects, setProjects] = useState<Projects['items']>([])
  const [projectsStatus, setProjectsStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading')
  const [project, setProject] = useState('')
  const [days, setDays] = useState('30')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [offset, setOffset] = useState(0)
  const [usage, setUsage] = useState<Usage | null>(null)
  const [usageOffset, setUsageOffset] = useState(0)
  const [printRows, setPrintRows] = useState<Page['items']>([])
  const [printUsage, setPrintUsage] = useState<Usage['items']>([])
  const flight = useRef(false)
  useEffect(() => {
    let active = true
    Promise.all([productRequest<Projects>('/projects?archived=false&limit=100'), productRequest<Projects>('/projects?archived=true&limit=100')]).then(values => { if (active) { setProjects(values.flatMap(value => value.items)); setProjectsStatus('ready') } }).catch(() => { if (active) setProjectsStatus('unavailable') })
    return () => { active = false }
  }, [])
  useEffect(() => {
    if (!viewId) return
    let active = true
    Promise.all([productRequest<Summary>(`/reporting/views/${viewId}`), productRequest<Page>(`/reporting/views/${viewId}/runs?offset=${offset}`)])
      .then(([value, page]) => { if (active) { setSummary(value); setRows(page) } })
      .catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Chưa đọc được tổng quan.') })
    return () => { active = false }
  }, [viewId, offset])
  useEffect(() => {
    if (!viewId) return
    let active = true
    productRequest<Usage>(`/reporting/views/${viewId}/usage?offset=${usageOffset}`).then(value => { if (active) setUsage(value) }).catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Chưa đọc được usage.') })
    return () => { active = false }
  }, [viewId, usageOffset])
  async function apply(event?: React.FormEvent) {
    event?.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError('')
    try {
      const value = await productRequest<Summary>('/reporting/views', 'POST', {
        project_id: project || null, status: status || null,
        start: new Date(Date.now() - Number(days) * 86400000).toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      })
      setSummary(value); setRows(null); setOffset(0); setUsageOffset(0); setPrintRows([]); setPrintUsage([]); setParams({ view: value.snapshot_id })
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa tạo được tổng quan.') }
    finally { flight.current = false; setBusy(false) }
  }
  async function csv() {
    if (!summary || flight.current) return
    flight.current = true; setBusy(true); setError('')
    try { download(await productDownload(`/reporting/views/${summary.snapshot_id}/csv`), 'smartregression-runs.csv') }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa xuất được CSV.') }
    finally { flight.current = false; setBusy(false) }
  }
  const current = summary?.snapshot_id === viewId ? summary : null
  async function print() {
    if (!current || current.total_runs > 10000 || flight.current) return
    flight.current = true; setBusy(true); setError('')
    try {
      const items: Page['items'] = []
      for (let index = 0; index < current.stored_rows; index += 100) {
        const page = await productRequest<Page>(`/reporting/views/${current.snapshot_id}/runs?offset=${index}&limit=100`)
        items.push(...page.items)
      }
      const usageItems: Usage['items'] = []
      for (let index = 0; index < 10000; index += 100) {
        const page = await productRequest<Usage>(`/reporting/views/${current.snapshot_id}/usage?offset=${index}&limit=100`)
        usageItems.push(...page.items)
        if (!page.next_cursor) break
        if (index === 9900) throw new Error('Usage vượt giới hạn bản in 10000 dòng.')
      }
      flushSync(() => { setPrintRows(items); setPrintUsage(usageItems) })
      window.print()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa chuẩn bị được bản in.') }
    finally { flight.current = false; setBusy(false) }
  }
  return <section className="dashboard-page"><div className="page-title-row"><div><h1>Tổng quan</h1><p>Các dự án và kết quả phân tích của bạn.</p></div><Link className="primary-button" to="/app/projects">Mở dự án →</Link></div>
    {error && <FormNotice error>{error}</FormNotice>}
    <form className="auth-card dashboard-filters" onSubmit={apply} aria-busy={busy}><label>Dự án<select value={project} onChange={event => setProject(event.target.value)}><option value="">Tất cả dự án</option>{projects.map(item => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label><label>Thời gian<select value={days} onChange={event => setDays(event.target.value)}><option value="7">7 ngày</option><option value="30">30 ngày</option><option value="90">90 ngày</option></select></label><label>Trạng thái tĩnh<select value={status} onChange={event => setStatus(event.target.value)}><option value="">Tất cả</option>{['queued', 'running', 'completed', 'failed', 'interrupted'].map(value => <option key={value}>{value}</option>)}</select></label><button disabled={busy} className="primary-button">{busy ? 'Đang đọc…' : 'Cập nhật tổng quan'}</button></form>
    {!current && <div className="dashboard-start"><section className="auth-card dashboard-projects"><div className="section-heading"><h2>Tiếp tục với dự án</h2><Link to="/app/projects">Xem tất cả</Link></div>
      {projectsStatus === 'loading' ? <p role="status">Đang tải dự án…</p> : projectsStatus === 'unavailable' ? <p>Chưa đọc được danh sách dự án. <Link to="/app/projects">Mở trang dự án để thử lại.</Link></p> : projects.some(item => !item.archived) ? <ul>{projects.filter(item => !item.archived).slice(0, 3).map(item => <li key={item.id}><Link to={`/app/projects/${item.id}`}><span className="dashboard-project-icon"><WorkspaceIcon name="projects" /></span><span><strong>{item.title}</strong><small>{item.repository_url.replace('https://github.com/', '')}</small></span><span aria-hidden="true">→</span></Link></li>)}</ul> : <div className="dashboard-projects-empty"><WorkspaceIcon name="projects" /><p>Chưa có dự án đang hoạt động.</p><Link to="/app/projects">Tạo hoặc khôi phục dự án</Link></div>}
    </section><section className="auth-card dashboard-start-guide"><span className="dashboard-guide-icon"><WorkspaceIcon name="reports" /></span><h2>Xem lại kết quả phân tích</h2><p>Đã có file JSON? Mở báo cáo để đọc kết quả và bằng chứng đã xuất.</p><Link className="secondary-action" to="/reports">Mở báo cáo đã lưu</Link><div className="dashboard-filter-help"><strong>Biểu đồ hoạt động và trạng thái</strong><p>Xem xu hướng theo ngày, trạng thái phân tích tĩnh và AI từ các lượt đã lưu. Áp dụng bộ lọc đang chọn ở phía trên.</p><button type="button" disabled={busy} onClick={() => void apply()}>{busy ? 'Đang tải biểu đồ…' : 'Xem biểu đồ'}</button></div></section></div>}
    {current && <><div className="report-provenance"><h2>Snapshot báo cáo</h2><p>Chốt lúc {new Date(current.filters.as_of).toLocaleString()} · múi giờ {current.filters.timezone}</p><p>{current.filters.start} → {current.filters.end} · project {current.filters.project_id ?? 'tất cả'} · status {current.filters.status ?? 'tất cả'}</p></div>
      <div className="dashboard-kpis">{[['Lượt phân tích', current.total_runs], ['Dự án có run', current.project_count], ['Chi phí đã biết (USD)', current.known_actual_micro_usd == null ? 'N/A' : (current.known_actual_micro_usd / 1e6).toFixed(6)], ['Bản ghi chưa biết chi phí', current.unknown_actual_count]].map(([label, value]) => <a href={label === 'Lượt phân tích' || label === 'Dự án có run' ? '#dashboard-runs' : '#dashboard-usage'} className="auth-card" key={label}><span>{label}</span><strong>{value}</strong><small>Xem bản ghi cùng bộ lọc ↓</small></a>)}</div>
      <p>Khoản giữ chỗ chưa quyết toán: {(current.reservation_micro_usd / 1e6).toFixed(6)} USD. Đây không phải chi phí thực tế.</p>
      <DashboardCharts summary={current} />
      <div className="dialog-actions dashboard-actions"><button disabled={busy || current.total_runs > 10000} onClick={() => void csv()}>Xuất toàn bộ CSV theo bộ lọc</button><button disabled={busy || current.total_runs > 10000} onClick={() => void print()}>In / Lưu PDF</button></div>
      <section className="auth-card" id="dashboard-runs"><h2>Run trong snapshot</h2><div className="screen-only"><RunTable items={rows?.items ?? []} /></div><div className="print-only"><RunTable items={printRows} /></div>{rows?.items.length === 0 && <p>Không có run khớp bộ lọc.</p>}<div className="dialog-actions dashboard-actions"><button disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 25))}>Trang trước</button><button disabled={!rows?.next_cursor} onClick={() => setOffset(value => value + 25)}>Trang tiếp</button></div></section>
      <section id="dashboard-usage" className="auth-card"><h2>Usage AI cùng snapshot</h2><div className="screen-only"><UsageTable items={usage?.items ?? []} /></div><div className="print-only"><UsageTable items={printUsage} /></div><div className="dialog-actions dashboard-actions"><button disabled={usageOffset === 0} onClick={() => setUsageOffset(value => Math.max(0, value - 25))}>Usage trước</button><button disabled={!usage?.next_cursor} onClick={() => setUsageOffset(value => value + 25)}>Usage tiếp</button></div></section>
      <ul className="report-limitations">{current.limitations.map(item => <li key={item}>{item}</li>)}</ul><p>Snapshot hết hạn sau 24 giờ; refresh dữ liệu bằng nút Cập nhật tổng quan.</p>
    </>}
  </section>
}
