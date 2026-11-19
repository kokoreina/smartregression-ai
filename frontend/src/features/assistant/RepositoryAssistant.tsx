import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { components } from '../../types/generated'
import { productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'
import { CoverageDetails } from '../explorer/CoverageDetails'
import './assistant.css'

type Reply = components['schemas']['AssistantReply']
type Thread = components['schemas']['AssistantThread']
type Message = components['schemas']['AssistantMessage']
type Watch = components['schemas']['RepositoryWatch']
type Notification = components['schemas']['ChangeNotification']
type Proof = components['schemas']['GraphEvidence']
type MessageInput = components['schemas']['MessageCreate']

function errorText(cause: unknown) { return cause instanceof Error ? cause.message : 'Chưa hoàn tất yêu cầu. Hãy thử lại.' }

function Citation({ proof, projectId }: { proof: Proof; projectId: string }) {
  const params = new URLSearchParams({ section: 'explorer', commit: proof.commit, path: proof.path })
  return <Link className="assistant-citation" to={`/app/projects/${projectId}?${params}`}>
    {proof.path}{proof.line_start ? `:${proof.line_start}${proof.line_end !== proof.line_start ? `–${proof.line_end}` : ''}` : ''}
    <span> · {proof.commit.slice(0, 8)}</span>
  </Link>
}

function ReplyView({ value, projectId }: { value: Reply; projectId: string }) {
  const facts = value.facts ?? []
  const pieces = value.excerpts ?? []
  return <div className="assistant-reply"><p>{value.summary}</p>
    {facts.length > 0 && <details className="assistant-facts"><summary>{facts.length} bằng chứng và vị trí đọc mã</summary>
      <ul>{facts.map((fact, index) => <li key={index}><p>{fact.text}</p><div className="assistant-citations">{(fact.evidence ?? []).map(proof => <Citation key={proof.id} proof={proof} projectId={projectId} />)}</div></li>)}</ul>
    </details>}
    {pieces.length > 0 && <details className="assistant-excerpts"><summary>Xem trích đoạn nguồn ({pieces.length})</summary>{pieces.map(piece => <div key={piece.path}><p><strong>{piece.path}</strong> · dòng {piece.line_start}–{piece.line_end}</p><pre><code>{piece.content}</code></pre></div>)}</details>}
    <details className="assistant-limits"><summary>Giới hạn của câu trả lời</summary><ul>{value.limitations.map((line, index) => <li key={index}>{line}</li>)}</ul><CoverageDetails coverage={value.coverage} compact /></details>
  </div>
}

export function RepositoryAssistant({ projectId, repositoryUrl, archived }: { projectId: string; repositoryUrl: string; archived: boolean }) {
  const base = `/projects/${projectId}/assistant`
  const [overview, setOverview] = useState<Reply | null>(null)
  const [threads, setThreads] = useState<Thread[]>([])
  const [threadId, setThreadId] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [action, setAction] = useState<MessageInput['action']>('chat')
  const [ai, setAi] = useState(false)
  const [allowFallback, setAllowFallback] = useState(false)
  const [excerptConsent, setExcerptConsent] = useState(false)
  const [draftEvidence, setDraftEvidence] = useState<{ signature: string; reply: Reply } | null>(null)
  const [watch, setWatch] = useState<Watch | null>(null)
  const [branch, setBranch] = useState('')
  const [paths, setPaths] = useState('')
  const [automatic, setAutomatic] = useState(false)
  const [interval, setIntervalSeconds] = useState(600)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const flight = useRef(false)
  const alive = useRef(true)
  const messageKey = useRef<{ signature: string; key: string } | null>(null)
  const threadKey = useRef(crypto.randomUUID())
  const activeThread = threads.find(value => value.id === threadId)
  const currentCommit = activeThread?.commit ?? overview?.commit
  const draftSignature = JSON.stringify({ question: question.trim(), action, commit: currentCommit })
  const preview = draftEvidence?.signature === draftSignature ? draftEvidence.reply : null

  useEffect(() => {
    alive.current = true
    let active = true
    async function load() {
      const results = await Promise.allSettled([
        productRequest<Reply>(`${base}/overview`, 'POST', {}),
        productRequest<Thread[]>(`${base}/threads`),
        productRequest<Watch | null>(`${base}/watch`),
        productRequest<Notification[]>(`${base}/notifications`),
        productRequest<components['schemas']['RepositoryOverview']>(`/projects/${projectId}/repository`),
      ])
      if (!active) return
      const [summary, conversations, tracking, notes, repo] = results
      if (summary.status === 'fulfilled') setOverview(summary.value)
      if (conversations.status === 'fulfilled') setThreads(conversations.value)
      if (tracking.status === 'fulfilled') {
        setWatch(tracking.value)
        if (tracking.value) { setBranch(tracking.value.branch); setPaths(tracking.value.paths.join('\n')); setAutomatic(tracking.value.automatic); setIntervalSeconds(tracking.value.interval_seconds) }
        else if (repo.status === 'fulfilled') setBranch(repo.value.default_branch)
      }
      if (notes.status === 'fulfilled') setNotifications(notes.value)
      const failure = results.find(result => result.status === 'rejected')
      if (failure?.status === 'rejected') setError(errorText(failure.reason))
      setLoading(false)
    }
    void load()
    return () => { active = false; alive.current = false }
  }, [base, projectId])

  useEffect(() => {
    if (!threadId) return
    let active = true
    let timer: ReturnType<typeof setTimeout> | undefined
    async function load() {
      try {
        const values = await productRequest<Message[]>(`${base}/threads/${threadId}/messages`)
        if (!active) return
        setMessages(values)
        if (values.some(value => value.ai?.status === 'queued' || value.ai?.status === 'running')) timer = setTimeout(() => { void load() }, 1500)
      } catch (cause) { if (active) setError(errorText(cause)) }
    }
    void load()
    return () => { active = false; clearTimeout(timer) }
  }, [base, threadId, busy])

  useEffect(() => {
    if (!checking) return
    let active = true
    let timer: ReturnType<typeof setTimeout> | undefined
    let polls = 0
    async function poll() {
      try {
        const [value, notes] = await Promise.all([
          productRequest<Watch>(`${base}/watch`), productRequest<Notification[]>(`${base}/notifications`),
        ])
        if (!active) return
        setWatch(value); setNotifications(notes)
        if (value.pending && ++polls < 150) timer = setTimeout(() => { void poll() }, 2000)
        else { setChecking(false); setNotice(value.error_code ? 'Kiểm tra chưa hoàn tất. Baseline cũ được giữ lại.' : value.pending ? 'Tác vụ vẫn nằm trong hàng đợi. Có thể mở lại trang để xem kết quả.' : 'Đã đồng bộ nhánh. Nếu không có thay đổi, hệ thống không tạo thông báo mới.') }
      } catch (cause) { if (active) { setError(errorText(cause)); setChecking(false) } }
    }
    timer = setTimeout(() => { void poll() }, 1000)
    return () => { active = false; clearTimeout(timer) }
  }, [base, checking])

  useEffect(() => {
    if (!watch?.automatic || checking) return
    let active = true
    const timer = setInterval(() => {
      void Promise.all([productRequest<Notification[]>(`${base}/notifications`), productRequest<Watch>(`${base}/watch`)])
        .then(([notes, value]) => { if (active) { setNotifications(notes); setWatch(value) } })
        .catch(cause => { if (active) setError(errorText(cause)) })
    }, 30000)
    return () => { active = false; clearInterval(timer) }
  }, [base, watch?.automatic, checking])

  async function ensureThread(commit: string) {
    if (activeThread?.commit === commit) return activeThread
    const value = await productRequest<Thread>(`${base}/threads`, 'POST', { commit, title: `Đọc mã · ${commit.slice(0, 8)}`, idempotency_key: threadKey.current })
    if (!alive.current) throw new Error('Trang đã được đóng.')
    setThreads(old => [value, ...old.filter(item => item.id !== value.id)]); setThreadId(value.id)
    return value
  }

  async function send(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current || !currentCommit || !question.trim()) return
    flight.current = true; setBusy(true); setError(''); setNotice('')
    try {
      const thread = await ensureThread(currentCommit)
      const input = { question: question.trim(), action, use_llm: ai, allow_metadata_egress: ai,
        allow_model_fallback: ai && allowFallback,
        allow_excerpt_egress: ai && excerptConsent,
        excerpts: ai && excerptConsent ? (preview?.excerpts ?? []).map(piece => ({ path: piece.path, start: piece.line_start, end: piece.line_end })) : [] }
      const signature = JSON.stringify({ ...input, thread: thread.id })
      if (messageKey.current?.signature !== signature) messageKey.current = { signature, key: crypto.randomUUID() }
      const value = await productRequest<Message>(`${base}/threads/${thread.id}/messages`, 'POST', { ...input, idempotency_key: messageKey.current.key })
      if (!alive.current) return
      setMessages(old => [...old.filter(item => item.id !== value.id), value]); setQuestion(''); setExcerptConsent(false)
    } catch (cause) { if (alive.current) setError(errorText(cause)) }
    finally { flight.current = false; if (alive.current) setBusy(false) }
  }

  async function previewQuestion() {
    if (flight.current || !currentCommit || !question.trim()) return
    flight.current = true; setBusy(true); setError(''); setExcerptConsent(false)
    try {
      const thread = await ensureThread(currentCommit)
      const reply = await productRequest<Reply>(`${base}/threads/${thread.id}/preview`, 'POST', { question: question.trim(), action, idempotency_key: crypto.randomUUID() })
      if (alive.current) setDraftEvidence({ signature: draftSignature, reply })
    } catch (cause) { if (alive.current) setError(errorText(cause)) }
    finally { flight.current = false; if (alive.current) setBusy(false) }
  }

  async function saveWatch(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError(''); setNotice('')
    try {
      const result = await productRequest<Watch>(`${base}/watch`, 'PUT', { branch, paths: paths.split('\n').map(v => v.trim()).filter(Boolean), automatic, interval_seconds: interval, version: watch?.version ?? 0 })
      if (alive.current) { setWatch(result); setNotice('Đã lưu vùng theo dõi. Lượt đầu dùng commit hiện tại làm baseline; các lượt sau so sánh từ baseline này.') }
    } catch (cause) { if (alive.current) setError(errorText(cause)) }
    finally { flight.current = false; if (alive.current) setBusy(false) }
  }

  async function check() {
    if (checking || flight.current) return
    flight.current = true; setError(''); setNotice('')
    try { await productRequest<Watch>(`${base}/check`, 'POST', {}); if (alive.current) setChecking(true) }
    catch (cause) { if (alive.current) setError(errorText(cause)) }
    finally { flight.current = false }
  }

  async function newThread(commit = overview?.commit) {
    if (!commit || busy) return
    threadKey.current = crypto.randomUUID(); setThreadId(''); setMessages([]); setExcerptConsent(false)
    setBusy(true); setError('')
    try {
      const value = await productRequest<Thread>(`${base}/threads`, 'POST', { commit, title: `Đọc mã · ${commit.slice(0, 8)}`, idempotency_key: threadKey.current })
      if (alive.current) { setThreads(old => [value, ...old]); setThreadId(value.id) }
    } catch (cause) { if (alive.current) setError(errorText(cause)) }
    finally { if (alive.current) setBusy(false) }
  }

  async function markRead(note: Notification) {
    try { await productRequest(`${base}/notifications/${note.id}/read`, 'POST', {}); if (alive.current) setNotifications(old => old.map(item => item.id === note.id ? { ...item, read_at: new Date().toISOString() } : item)) }
    catch (cause) { if (alive.current) setError(errorText(cause)) }
  }

  return <div className="repo-assistant" aria-busy={loading}>
    <header className="assistant-heading"><div><h2>Hiểu mã nguồn, theo sát thay đổi</h2><p>Mọi câu trả lời gắn với một commit. Phân tích ảnh hưởng ưu tiên Python.</p></div>
      {currentCommit && <span className="assistant-sha">Commit <code>{currentCommit.slice(0, 8)}</code></span>}</header>
    {error && <FormNotice error>{error}</FormNotice>}{notice && <p className="assistant-notice" role="status">{notice}</p>}
    {loading && <p role="status">Đang chuẩn bị tổng quan và đọc lịch sử đã lưu…</p>}
    <div className="assistant-columns"><section className="assistant-main" aria-label="Trợ lý repository">
      {overview && <details className="assistant-overview" open={messages.length === 0}><summary>Tổng quan repository · {overview.commit.slice(0, 8)}</summary><ReplyView value={overview} projectId={projectId} /></details>}
      <div className="assistant-conversation-bar"><label htmlFor="assistant-thread">Hội thoại đã lưu<select id="assistant-thread" value={threadId} disabled={busy} onChange={event => { setThreadId(event.target.value); setMessages([]); setExcerptConsent(false) }}><option value="">Snapshot mới nhất</option>{threads.map(thread => <option key={thread.id} value={thread.id}>{thread.title} · {new Date(thread.created_at).toLocaleDateString('vi-VN')}</option>)}</select></label><button type="button" disabled={busy || !overview || archived} onClick={() => void newThread()}>Hội thoại mới</button></div>
      <div className="assistant-messages" aria-label="Nội dung hội thoại" aria-live="polite">
        {messages.length === 0 && !loading && <div className="assistant-empty"><h3>Bắt đầu từ điều bạn muốn hiểu</h3><p>Hỏi bằng tên file, symbol hoặc chức năng. Với câu hỏi về ảnh hưởng, hãy cấu hình vùng mã bạn phụ trách ở bên cạnh.</p><button type="button" onClick={() => { setQuestion('Giải thích tổng quan và thứ tự đọc repository này'); setAction('overview') }}>Giải thích tổng quan</button></div>}
        {messages.map(message => <article className="assistant-message" key={message.id}><h3>{message.question}</h3><span className="assistant-mode">Bằng chứng tĩnh · {message.reply.commit.slice(0, 8)}</span><ReplyView value={message.reply} projectId={projectId} />
          {message.ai && <div className="assistant-generated"><h4>Gemini · {message.ai.result?.model ?? (typeof message.ai.provenance?.requested_model === 'string' ? `yêu cầu ${message.ai.provenance.requested_model}` : 'Chưa nhận thông tin model')}</h4>
            {typeof message.ai.provenance?.attempt === 'number' && <p className="assistant-muted">Lượt {message.ai.provenance.attempt}/3 · mỗi lượt dùng quota riêng{message.ai.provenance.requested_model === 'gemini-3.5-flash-lite' ? ' · đã chọn model dự phòng' : ''}.</p>}
            {['queued', 'running'].includes(message.ai.status) && <p role="status">AI đang xử lý. Có thể mở lại hội thoại sau.</p>}
            {message.ai.result?.data && <><p>{message.ai.result.data.summary}</p>{message.ai.result.data.findings.map((finding, index) => <div key={index}><p>{finding.explanation}</p>{finding.evidence_ids.map(id => { const proof = (message.reply.facts ?? []).flatMap(fact => fact.evidence ?? []).find(item => item.id === id); return proof ? <Citation key={id} proof={proof} projectId={projectId} /> : <code key={id}>{id}</code> })}</div>)}<p className="assistant-muted">{message.ai.result.data.limitations.join(' ')}</p></>}
            {message.ai.status === 'failed' && (message.ai.result?.error_code === 'provider_unavailable'
              ? <div className="assistant-provider-unavailable" role="status"><p>Gemini đang tạm quá tải (503). Các lượt thử đã dừng theo giới hạn hoặc quota; chưa có câu trả lời AI. Bạn vẫn đọc được bằng chứng tĩnh.</p><button type="button" onClick={() => { setQuestion(message.question); setAi(true); setAllowFallback(false); setExcerptConsent(false); setAction(message.ai?.action === 'overview' || message.ai?.action === 'changes' ? message.ai.action : 'chat') }}>Soạn câu hỏi lại</button><small>Thao tác này chưa gọi API. Kiểm tra quota và gửi khi bạn muốn thử lại.</small></div>
              : <p role="alert">AI chưa hoàn tất ({message.ai.result?.error_code ?? 'unknown'}). Bằng chứng tĩnh vẫn được giữ.</p>)}
          </div>}
        </article>)}
      </div>
      <form className="assistant-composer" onSubmit={send} aria-busy={busy}><label htmlFor="assistant-question">Câu hỏi về dự án</label><textarea id="assistant-question" rows={3} maxLength={600} required value={question} disabled={busy || archived} onChange={event => { setQuestion(event.target.value); setExcerptConsent(false) }} placeholder="Ví dụ: hàm invoice được gọi ở đâu?" />
        <div className="assistant-composer-options"><label htmlFor="assistant-action">Phạm vi<select id="assistant-action" value={action} onChange={event => { setAction(event.target.value as MessageInput['action']); setExcerptConsent(false) }} disabled={busy}><option value="chat">Tìm và giải thích mã</option><option value="overview">Tổng quan repository</option><option value="changes">Thay đổi đã đồng bộ ở commit này</option></select></label>
          <label className="checkbox-label"><input type="checkbox" checked={ai} disabled={busy} onChange={event => { setAi(event.target.checked); setAllowFallback(false); setExcerptConsent(false) }} />Dùng Gemini 3.8 Flash; đồng ý gửi câu hỏi, metadata và tối đa 3 câu hỏi trước đó. Nếu gặp 503, thử tối đa 3 lượt trong quota.</label></div>
        {ai && <label className="checkbox-label"><input type="checkbox" checked={allowFallback} disabled={busy} onChange={event => setAllowFallback(event.target.checked)} />Cho phép dùng Gemini 3.5 Flash-Lite ở lượt cuối nếu 3.8 vẫn quá tải. Kết quả sẽ ghi rõ model đã dùng.</label>}
        {ai && <button type="button" disabled={busy || !currentCommit || !question.trim() || archived} onClick={() => void previewQuestion()}>Xem bằng chứng trước khi hỏi AI</button>}
        {ai && preview && (preview.excerpts ?? []).length > 0 && <details className="assistant-egress"><summary>Trích đoạn có thể gửi tới Gemini</summary><p>Mặc định chỉ gửi metadata. Các đoạn dưới đây chỉ được gửi khi bạn đồng ý riêng.</p>{(preview.excerpts ?? []).map(piece => <div key={piece.path}><p>{piece.path} · dòng {piece.line_start}–{piece.line_end}</p><pre><code>{piece.content}</code></pre></div>)}<label className="checkbox-label"><input type="checkbox" checked={excerptConsent} onChange={event => setExcerptConsent(event.target.checked)} disabled={busy} />Tôi đồng ý gửi đúng các trích đoạn đang hiển thị.</label></details>}
        <div className="assistant-send-row"><small>{ai ? 'Free tier vẫn có hạn mức. Không tự gửi lại khi thất bại.' : 'Tra cứu tĩnh trên máy chủ; không gọi Gemini.'}</small><button className="primary-button" disabled={busy || !currentCommit || !question.trim() || archived}>{busy ? 'Đang xử lý…' : ai ? 'Hỏi Gemini' : 'Tìm bằng chứng'}</button></div>
      </form>
    </section>
    <aside className="assistant-side" aria-label="Theo dõi thay đổi GitHub"><form className="assistant-watch" onSubmit={saveWatch}><h3>Phần mã tôi theo dõi</h3><p>Chọn vùng mã để đối chiếu thay đổi. Đây là phạm vi quan tâm, không tự xác nhận quyền sở hữu.</p>
      <label htmlFor="watch-branch">Nhánh GitHub</label><input id="watch-branch" value={branch} onChange={event => setBranch(event.target.value)} maxLength={200} required disabled={busy || archived} />
      <label htmlFor="watch-paths">File hoặc thư mục · mỗi dòng một đường dẫn</label><textarea id="watch-paths" rows={3} value={paths} onChange={event => setPaths(event.target.value)} disabled={busy || archived} placeholder={'Ví dụ: src/billing\ntests/test_billing.py'} /><small>Để trống để xem thay đổi chung; chưa có đánh giá cá nhân.</small>
      <label className="checkbox-label"><input type="checkbox" checked={automatic} onChange={event => setAutomatic(event.target.checked)} disabled={busy || archived} />Tự kiểm tra khi worker đang chạy</label>
      {automatic && <label htmlFor="watch-interval">Chu kỳ kiểm tra<select id="watch-interval" value={interval} onChange={event => setIntervalSeconds(Number(event.target.value))}><option value={300}>5 phút</option><option value={600}>10 phút</option><option value={1800}>30 phút</option></select></label>}
      <button type="submit" disabled={busy || !branch || archived}>Lưu theo dõi</button>
      {watch && <div className="assistant-sync-status"><p>Baseline <code>{watch.last_commit.slice(0, 8)}</code></p><p>{watch.checked_at ? `Đồng bộ: ${new Date(watch.checked_at).toLocaleString('vi-VN')}` : 'Chưa kiểm tra'}</p>{watch.error_code && <p role="alert">Chưa đồng bộ: {watch.error_code}. Baseline cũ được giữ lại.</p>}<button type="button" disabled={checking || busy || archived} onClick={() => void check()}>{checking ? 'Đang kiểm tra…' : 'Kiểm tra thay đổi mới'}</button><small>Máy chủ/worker ngừng chạy thì theo dõi sẽ tạm dừng. Các sự kiện gần nhau có thể được gộp.</small></div>}
    </form>
    <section className="assistant-notifications" aria-labelledby="change-notifications-title"><h3 id="change-notifications-title">Thay đổi đã phát hiện <span>{notifications.filter(note => !note.read_at).length} chưa đọc</span></h3>
      {notifications.length === 0 && <p>Chưa có thông báo. Lưu nhánh theo dõi rồi kiểm tra khi có commit mới.</p>}
      {notifications.map(note => <article className={`assistant-notification${note.read_at ? ' is-read' : ''}`} key={note.id}><h4>{note.report.branch} · {note.report.changes.length} file thay đổi</h4><p><code>{note.report.base.slice(0, 8)} → {note.report.target.slice(0, 8)}</code></p><time dateTime={note.created_at}>{new Date(note.created_at).toLocaleString('vi-VN')}</time>
        <p>{note.report.scope_impacts.length} file trong vùng theo dõi có liên hệ tĩnh.</p>{note.report.scope.length === 0 && <p>Chưa chọn vùng mã cá nhân.</p>}
        <details><summary>Xem thay đổi và đường ảnh hưởng</summary><ul>{note.report.changes.map(change => <li key={change.path}><code>{change.path}</code> · {({ added: 'thêm', modified: 'sửa', deleted: 'xóa', renamed: 'đổi tên' } as Record<string, string>)[change.change] ?? change.change}</li>)}</ul>
          {note.report.scope_impacts.map(item => <div className="assistant-impact-chain" key={item.path}><strong>{item.path}</strong><p>{item.relationship === 'changed' ? 'Thay đổi trực tiếp' : item.relationship === 'direct' ? 'Phụ thuộc trực tiếp' : 'Phụ thuộc gián tiếp'}</p><ol aria-label={`Đường ảnh hưởng tới ${item.path}`}>{item.chain.map(path => <li key={path}><code>{path}</code></li>)}</ol>{item.evidence.map(proof => <Citation key={proof.id} proof={proof} projectId={projectId} />)}</div>)}
          {note.report.impacts_truncated && <p>Danh sách/đường ảnh hưởng đã chạm giới hạn hiển thị.</p>}<p className="assistant-muted">{note.report.limitations.join(' ')}</p><CoverageDetails coverage={note.report.target_coverage} compact /></details>
        <div className="assistant-note-actions"><a href={`${repositoryUrl}/compare/${note.report.base}..${note.report.target}`} target="_blank" rel="noreferrer">Mở diff GitHub</a><button type="button" disabled={busy || archived} onClick={() => { void newThread(note.report.target); setAction('changes'); setQuestion('Các thay đổi mới có ảnh hưởng tới vùng mã tôi theo dõi như thế nào?') }}>Hỏi về thay đổi</button>{!note.read_at && <button type="button" onClick={() => void markRead(note)}>Đánh dấu đã đọc</button>}</div>
      </article>)}
    </section></aside></div>
  </div>
}
