import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import type { components } from '../../types/generated'
import { AccountError, productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'
import './projects.css'
import { ProjectRuns } from './Runs'
import { ResumeLink } from '../explorer/Notes'

type Project = components['schemas']['Project']
type Page = components['schemas']['ProjectPage']
type ActivityPage = components['schemas']['ActivityPage']

function errorMessage(error: unknown): string {
  if (error instanceof AccountError) {
    const messages: Record<string, string> = {
      active_project_limit: 'Bạn có tối đa 3 dự án đang hoạt động. Hãy lưu trữ một dự án trước.',
      version_conflict: 'Dự án đã được cập nhật ở nơi khác. Hãy tải lại trước khi sửa.',
      repository_lookup_failed: 'Chưa truy cập được repo GitHub public. Kiểm tra URL, mạng hoặc giới hạn GitHub.',
      project_not_found: 'Dự án không tồn tại hoặc bạn không có quyền truy cập.',
      project_storage_unavailable: 'Dịch vụ dự án chưa sẵn sàng. Vui lòng thử lại sau.',
    }
    const message = messages[error.code]
    if (message) return message
  }
  return error instanceof Error ? error.message : 'Không thể hoàn tất yêu cầu.'
}

export function Projects() {
  const [items, setItems] = useState<Project[]>([])
  const [cursor, setCursor] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [archived, setArchived] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const [description, setDescription] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [refresh, setRefresh] = useState(0)
  const flight = useRef(false)
  const sequence = useRef(0)

  useEffect(() => {
    const generation = ++sequence.current
    let cancelled = false
    productRequest<Page>(`/projects?search=${encodeURIComponent(query)}&archived=${archived}`)
      .then(page => { if (!cancelled && generation === sequence.current) { setItems(page.items); setCursor(page.next_cursor ?? null) } })
      .catch(cause => { if (!cancelled) setError(errorMessage(cause)) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [query, archived, refresh])

  async function create(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError('')
    try {
      await productRequest<Project>('/projects', 'POST', { title, repository_url: url, description })
      setTitle(''); setUrl(''); setDescription(''); setShowCreate(false); setArchived(false); setLoading(true); setItems([]); setCursor(null); setRefresh(value => value + 1)
    } catch (cause) { setError(errorMessage(cause)) }
    finally { flight.current = false; setBusy(false) }
  }

  async function more() {
    if (!cursor || loading) return
    const generation = sequence.current
    setLoading(true)
    try {
      const page = await productRequest<Page>(`/projects?search=${encodeURIComponent(query)}&archived=${archived}&cursor=${encodeURIComponent(cursor)}`)
      if (generation === sequence.current) { setItems(old => [...old, ...page.items]); setCursor(page.next_cursor ?? null) }
    } catch (cause) { if (generation === sequence.current) setError(errorMessage(cause)) }
    finally { if (generation === sequence.current) setLoading(false) }
  }

  return <section className="projects-page"><p className="eyebrow">KHÔNG GIAN REPOSITORY</p>
    <div className="page-title-row"><div><h1>Dự án của tôi</h1><p>Khám phá cấu trúc, lưu phân tích và tiếp tục công việc trên repo của bạn.</p></div>
      <button className="primary-button" onClick={() => setShowCreate(value => !value)} aria-expanded={showCreate}>{showCreate ? 'Đóng form' : '+ Tạo dự án'}</button></div>
    {error && <FormNotice error>{error}</FormNotice>}
    {showCreate && <form className="auth-card project-create" onSubmit={create} aria-busy={busy}><h2>Dự án mới</h2>
      <label htmlFor="project-title">Tên dự án</label><input id="project-title" value={title} onChange={e => setTitle(e.target.value)} required maxLength={120} disabled={busy} />
      <label htmlFor="project-url">URL repo GitHub public</label><input id="project-url" type="url" value={url} onChange={e => setUrl(e.target.value)} required maxLength={240} placeholder="https://github.com/owner/repository" disabled={busy} />
      <p className="field-hint">Mỗi dự án gắn cố định một repo. Tối đa 3 dự án đang hoạt động.</p>
      <label htmlFor="project-description">Mô tả</label><textarea id="project-description" value={description} onChange={e => setDescription(e.target.value)} maxLength={2000} disabled={busy} />
      <button className="primary-button" disabled={busy}>{busy ? 'Đang kiểm tra và tạo…' : 'Tạo dự án'}</button></form>}
    <form className="project-filters" onSubmit={event => { event.preventDefault(); if (query !== search) { setLoading(true); setError(''); setItems([]); setCursor(null); setQuery(search) } }}>
      <label htmlFor="project-search">Tìm dự án</label><input id="project-search" value={search} onChange={e => setSearch(e.target.value)} maxLength={120} placeholder="Tên dự án hoặc repo" />
      <button>Tìm kiếm</button><label className="checkbox-label"><input type="checkbox" checked={archived} onChange={e => { setLoading(true); setError(''); setItems([]); setCursor(null); setArchived(e.target.checked) }} />Đã lưu trữ</label>
    </form>
    {loading && <p role="status">Đang tải dự án…</p>}
    {!loading && !error && items.length === 0 && <div className="auth-card empty-workspace"><h2>{archived ? 'Chưa có dự án đã lưu trữ' : 'Bắt đầu với repo đầu tiên'}</h2><p>{query ? 'Không có dự án khớp từ khóa.' : 'Tạo dự án bằng URL GitHub public để bắt đầu khám phá.'}</p></div>}
    <div className="project-grid">{items.map(project => <article className="auth-card project-card" key={project.id}><span className="status-pill">{project.archived ? 'Đã lưu trữ' : 'Đang hoạt động'}</span>
      <h2><Link to={`/app/projects/${project.id}`}>{project.title}</Link></h2><p className="repository-url">{project.repository_url.replace('https://github.com/', '')}</p><p>{project.description || 'Chưa có mô tả.'}</p>
      <Link className="text-link" to={`/app/projects/${project.id}`}>Mở dự án →</Link></article>)}</div>
    {cursor && <button disabled={loading} onClick={() => void more()}>Tải thêm dự án</button>}
  </section>
}

export function ProjectDetail() {
  const { projectId } = useParams()
  const [project, setProject] = useState<Project | null>(null)
  const [activity, setActivity] = useState<ActivityPage | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [refresh, setRefresh] = useState(0)
  const flight = useRef(false)
  useEffect(() => {
    let cancelled = false
    Promise.all([productRequest<Project>(`/projects/${projectId}`), productRequest<ActivityPage>(`/projects/${projectId}/activity`)])
      .then(([data, events]) => { if (!cancelled) { setProject(data); setTitle(data.title); setDescription(data.description); setActivity(events) } })
      .catch(cause => { if (!cancelled) setError(errorMessage(cause)) })
    return () => { cancelled = true }
  }, [projectId, refresh])

  async function mutate(action: 'update' | 'archive' | 'restore') {
    if (!project || flight.current) return
    flight.current = true; setBusy(true); setError('')
    try {
      const data = await productRequest<Project>(`/projects/${project.id}${action === 'update' ? '' : '/' + action}`, action === 'update' ? 'PATCH' : 'POST', {
        version: project.version, ...(action === 'update' ? { title, description } : {}),
      })
      setProject(data); setRefresh(old => old + 1)
    } catch (cause) { setError(errorMessage(cause)) }
    finally { flight.current = false; setBusy(false) }
  }
  async function moreActivity() {
    if (!activity?.next_cursor || flight.current) return
    flight.current = true; setBusy(true)
    try { const page = await productRequest<ActivityPage>(`/projects/${projectId}/activity?cursor=${encodeURIComponent(activity.next_cursor)}`); setActivity(old => old ? { items: [...old.items, ...page.items], next_cursor: page.next_cursor } : page) }
    catch (cause) { setError(errorMessage(cause)) }
    finally { flight.current = false; setBusy(false) }
  }
  return <section className="project-detail"><Link to="/app/projects">← Dự án của tôi</Link>
    {error && <FormNotice error>{error}</FormNotice>}
    {!project || project.id !== projectId ? !error && <p role="status">Đang tải dự án…</p> : <><p className="eyebrow">{project.archived ? 'DỰ ÁN ĐÃ LƯU TRỮ' : 'DỰ ÁN CÁ NHÂN'}</p><h1>{project.title}</h1>
      <p className="repository-url">{project.repository_url}</p>
      <Link className="text-link" to={`/app/projects/${project.id}/explorer`}>Mở Explorer: cây thư mục và graph →</Link>
      <ResumeLink projectId={project.id} />
      <p><Link className="text-link" to={`/app/projects/${project.id}/what-if`}>What-if và so sánh A/B →</Link></p>
      <ProjectRuns key={project.id} projectId={project.id} archived={project.archived} />
      <form className="auth-card project-create" onSubmit={event => { event.preventDefault(); void mutate('update') }} aria-busy={busy}>
        <h2>Cấu hình dự án</h2><label htmlFor="edit-title">Tên dự án</label><input id="edit-title" value={title} onChange={e => setTitle(e.target.value)} required maxLength={120} disabled={busy} />
        <label htmlFor="edit-description">Mô tả</label><textarea id="edit-description" value={description} onChange={e => setDescription(e.target.value)} maxLength={2000} disabled={busy} />
        <div className="dialog-actions"><button type="button" disabled={busy} onClick={() => void mutate(project.archived ? 'restore' : 'archive')}>{project.archived ? 'Khôi phục dự án' : 'Lưu trữ dự án'}</button>
          <button className="primary-button" disabled={busy}>Lưu thay đổi</button></div><p className="field-hint">Lưu trữ giữ nguyên lịch sử. Repo của dự án được giữ cố định.</p></form>
      <div className="auth-card activity-card"><h2>Hoạt động gần đây</h2><ul>{activity?.items.map(item => <li key={item.id}><span>{({ project_created: 'Tạo dự án', project_updated: 'Cập nhật dự án', project_archived: 'Lưu trữ dự án', project_restored: 'Khôi phục dự án' } as Record<string, string>)[item.action] ?? item.action}</span><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString('vi-VN')}</time></li>)}</ul>{activity?.next_cursor && <button disabled={busy} onClick={() => void moreActivity()}>Tải thêm hoạt động</button>}</div>
    </>}
  </section>
}
