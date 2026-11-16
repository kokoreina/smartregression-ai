import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { components } from '../../types/generated'
import { productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'

type Note = components['schemas']['Note']
type Page = components['schemas']['NotePage']
type State = components['schemas']['ViewState']

export function ResumeLink({ projectId }: { projectId: string }) {
  const [state, setState] = useState<State | null>(null)
  useEffect(() => {
    let active = true
    productRequest<State | null>(`/projects/${projectId}/view-state`).then(value => { if (active) setState(value) }).catch(() => undefined)
    return () => { active = false }
  }, [projectId])
  return state ? <p><Link className="text-link" to={`/app/projects/${projectId}/explorer?commit=${state.commit}${state.path ? '&path=' + encodeURIComponent(state.path) : ''}`}>Tiếp tục tại {state.path ?? state.commit.slice(0, 12)} →</Link>{state.stale && <span> · Đường dẫn cũ không còn trong snapshot.</span>}</p> : null
}

export function Notes({ projectId, commit, path }: { projectId: string; commit: string; path: string }) {
  const [notes, setNotes] = useState<Note[]>([])
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [kind, setKind] = useState<'note' | 'pin'>('note')
  const [editing, setEditing] = useState<Note | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [cursor, setCursor] = useState<string | null>(null)
  const [refresh, setRefresh] = useState(0)
  const flight = useRef(false)
  useEffect(() => {
    let active = true
    productRequest<Page>(`/projects/${projectId}/notes?current=${commit}`)
      .then(value => { if (active) { setNotes(value.items); setCursor(value.next_cursor ?? null) } })
      .catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Không đọc được ghi chú.') })
    return () => { active = false }
  }, [projectId, commit, refresh])

  async function save(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current || (!path && !editing)) return
    flight.current = true; setBusy(true); setError('')
    try {
      if (editing) await productRequest<Note>(`/projects/${projectId}/notes/${editing.id}`, 'PATCH', { version: editing.version, title, body, archived: false })
      else await productRequest<Note>(`/projects/${projectId}/notes`, 'POST', { kind, commit, path, title, body })
      setTitle(''); setBody(''); setEditing(null); setRefresh(value => value + 1)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa lưu được ghi chú.') }
    finally { flight.current = false; setBusy(false) }
  }

  async function archive(note: Note) {
    if (flight.current) return
    flight.current = true; setBusy(true); setError('')
    try { await productRequest<Note>(`/projects/${projectId}/notes/${note.id}`, 'PATCH', { version: note.version, title: note.title, body: note.body, archived: true }); setRefresh(value => value + 1) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa lưu trữ được ghi chú.') }
    finally { flight.current = false; setBusy(false) }
  }

  async function more() {
    if (!cursor || flight.current) return
    flight.current = true; setBusy(true)
    try { const value = await productRequest<Page>(`/projects/${projectId}/notes?current=${commit}&cursor=${encodeURIComponent(cursor)}`); setNotes(old => [...old, ...value.items]); setCursor(value.next_cursor ?? null) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Chưa tải được ghi chú.') }
    finally { flight.current = false; setBusy(false) }
  }

  return <details className="explorer-notes"><summary>Ghi chú và ghim ({notes.length}{cursor ? '+' : ''})</summary>{error && <FormNotice error>{error}</FormNotice>}
    <form onSubmit={save} className="notes-form" aria-busy={busy}><label htmlFor="note-kind">Loại</label><select id="note-kind" value={kind} disabled={busy || !!editing} onChange={e => setKind(e.target.value === 'pin' ? 'pin' : 'note')}><option value="note">Ghi chú</option><option value="pin">Ghim vị trí</option></select>
      <p className="field-hint">Vị trí: {editing?.path ?? (path || 'Hãy chọn file trước')} · {(editing?.commit ?? commit).slice(0, 12)}</p>
      <label htmlFor="note-title">Tiêu đề ghi chú</label><input id="note-title" value={title} onChange={e => setTitle(e.target.value)} required maxLength={120} disabled={busy} />
      <label htmlFor="note-body">Nội dung ghi chú</label><textarea id="note-body" value={body} onChange={e => setBody(e.target.value)} maxLength={10000} disabled={busy} />
      <button disabled={busy || (!path && !editing)}>{editing ? 'Lưu chỉnh sửa ghi chú' : 'Lưu ghi chú / ghim'}</button>{editing && <button type="button" onClick={() => { setEditing(null); setTitle(''); setBody('') }}>Hủy chỉnh sửa</button>}</form>
    <ul className="notes-list">{notes.map(note => <li key={note.id}><strong>{note.kind === 'pin' ? 'Ghim: ' : ''}{note.title}</strong><p>{note.body}</p>
      <Link to={`/app/projects/${projectId}/explorer?commit=${note.commit}&path=${encodeURIComponent(note.path)}`}>{note.path} · {note.commit.slice(0, 8)}</Link>
      {note.stale && <p>Đường dẫn này không còn ở snapshot đang xem; mở liên kết để quay lại SHA gốc.</p>}
      <div className="dialog-actions"><button disabled={busy} onClick={() => { setEditing(note); setTitle(note.title); setBody(note.body ?? ''); setKind(note.kind ?? 'note') }}>Sửa</button><button disabled={busy} onClick={() => void archive(note)}>Lưu trữ ghi chú</button></div></li>)}</ul>
    {cursor && <button disabled={busy} onClick={() => void more()}>Tải thêm ghi chú</button>}
  </details>
}
