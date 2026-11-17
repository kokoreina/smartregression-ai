import { useEffect, useRef, useState, type ChangeEvent, type FormEvent, type RefObject } from 'react'
import { StageReportView } from '../reports/StageReportView'
import { analysisValue, overviewValue, post, messages, type Overview, type Result } from './repositoryClient'
import { RepositoryTreeView } from './RepositoryTreeView'
import { treeValue, type GitTree } from './repositoryTree'
import { exportReport, loadRepositoryReport } from './repositoryReport'

export function RepositoryAnalysis() {
  const [url, setUrl] = useState('https://github.com/andialbrecht/sqlparse')
  const [repository, setRepository] = useState<Overview | null>(null)
  const [base, setBase] = useState('')
  const [target, setTarget] = useState('')
  const [question, setQuestion] = useState('Giải thích cấu trúc dự án và ảnh hưởng của các file thay đổi.')
  const [useLlm, setUseLlm] = useState(false)
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState<Result | null>(null)
  const [tree, setTree] = useState<GitTree | null>(null)
  const [saved, setSaved] = useState(false)
  const [exportedAt, setExportedAt] = useState<string | null>(null)
  const controller = useRef<AbortController | null>(null)
  const requestId = useRef(0)
  const inFlight = useRef(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const resultHeading = useRef<HTMLHeadingElement>(null)
  useEffect(() => () => { ++requestId.current; inFlight.current = false; controller.current?.abort() }, [])

  async function run(action: 'inspect' | 'tree' | 'analyze') {
    if (inFlight.current) return
    inFlight.current = true
    const id = ++requestId.current
    const active = () => id === requestId.current
    const requested = { repository_url: repository?.repository_url, base, target,
      use_llm: useLlm, allow_metadata_egress: useLlm && consent, question }
    controller.current?.abort()
    const current = new AbortController()
    controller.current = current
    const timeout = window.setTimeout(() => current.abort(), 120000)
    setError('')
    if (action !== 'tree') { setResult(null); setSaved(false); setExportedAt(null) }
    setBusy(action === 'analyze' ? 'Đang tải snapshot, phân tích Python và gọi Gemini nếu được chọn…' : 'Đang đọc cấu trúc và commit từ GitHub…')
    async function readTree(repositoryUrl: string, commit: string) {
      setTree(null)
      if (!commit) throw new Error('Repo chưa có commit để hiển thị cây thư mục.')
      const nextTree = treeValue(await post('/repositories/tree', { repository_url: repositoryUrl, commit }, current.signal), repositoryUrl, commit)
      if (active()) setTree(nextTree)
    }
    try {
      if (action === 'inspect') {
        setRepository(null)
        setTree(null)
        const value = overviewValue(await post('/repositories/inspect', { repository_url: url }, current.signal))
        if (!active()) return
        setRepository(value)
        setTarget(value.commits[0]?.sha ?? '')
        setBase(value.commits[1]?.sha ?? value.commits[0]?.sha ?? '')
        await readTree(value.repository_url, value.commits[0]?.sha ?? '')
      } else if (action === 'tree' && repository) {
        await readTree(repository.repository_url, target)
      } else {
        const value = analysisValue(await post('/repository-analyses', requested, current.signal))
        if (!active()) return
        if (value.report.identity.base.commit !== requested.base || value.report.identity.target.commit !== requested.target
          || value.repository.repository_url !== requested.repository_url) {
          throw new Error('Commit trong báo cáo không khớp yêu cầu.')
        }
        setResult(value)
        window.setTimeout(() => { if (active()) resultHeading.current?.focus() }, 0)
      }
    } catch (e) {
      if (active()) setError(current.signal.aborted ? 'Đã hết thời gian chờ. Backend có thể vẫn đang hoàn tất lượt này; chưa gửi lại yêu cầu ngay.'
        : e instanceof Error ? e.message : 'Không hoàn tất yêu cầu.')
    } finally {
      window.clearTimeout(timeout)
      if (active()) { inFlight.current = false; setBusy('') }
    }
  }

  function inspect(event: FormEvent) { event.preventDefault(); void run('inspect') }
  function analyze(event: FormEvent) { event.preventDefault(); void run('analyze') }
  function chooseTarget(sha: string) { setTarget(sha); setTree(null); setResult(null) }
  async function openReport(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file || inFlight.current) return
    inFlight.current = true
    const id = ++requestId.current
    setError('')
    setBusy('Đang kiểm tra báo cáo đã lưu…')
    try {
      const report = await loadRepositoryReport(file)
      if (id !== requestId.current) return
      setResult(report.result)
      setSaved(true)
      setExportedAt(report.exportedAt)
      window.setTimeout(() => { if (id === requestId.current) resultHeading.current?.focus() }, 0)
    } catch (e) {
      if (id === requestId.current) setError(e instanceof Error ? e.message : 'Không mở được báo cáo.')
    } finally {
      if (id === requestId.current) { inFlight.current = false; setBusy('') }
    }
  }
  function download() {
    if (!result) return
    const objectUrl = URL.createObjectURL(new Blob([JSON.stringify(exportReport(result), null, 2)], { type: 'application/json' }))
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = `analysis-${result.report.identity.run_id}.json`
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
  }

  return <section aria-labelledby="repository-heading" className="repository-analysis">
    <div className="card">
      <p className="eyebrow">PHÂN TÍCH REPOSITORY THẬT</p>
      <h2 id="repository-heading">Chọn GitHub repo và xem ảnh hưởng thay đổi</h2>
      <p>Nhập link repo public để xem cây thư mục và file. Chọn hai commit khi muốn phân tích ảnh hưởng Python và nhận giải thích từ Gemini.</p>
      <ol className="workflow-steps" aria-label="Quy trình phân tích">
        <li>1. Đọc repo và khám phá cây</li><li>2. Chọn hai commit</li><li>3. Phân tích và xem bằng chứng</li><li>4. Lưu báo cáo</li>
      </ol>
      <div className="saved-report-toolbar">
        <button type="button" disabled={!!busy} onClick={() => fileInput.current?.click()}>Mở báo cáo đã lưu</button>
        <span className="muted">Xem lại JSON gồm cả giải thích AI; không gọi GitHub hoặc Gemini.</span>
        <input ref={fileInput} type="file" accept=".json,application/json" hidden onChange={e => { void openReport(e) }} />
      </div>
      <form onSubmit={inspect} className="repo-form">
        <label htmlFor="repository-url">GitHub repository URL</label>
        <div className="repo-input-row">
          <input id="repository-url" type="url" required maxLength={240} disabled={!!busy} value={url}
            onChange={e => { setUrl(e.target.value); setRepository(null); setResult(null); setTree(null); setConsent(false) }}
            placeholder="https://github.com/owner/repository" />
          <button className="primary" disabled={!!busy} type="submit">Đọc repository</button>
        </div>
      </form>
      {repository && <form onSubmit={analyze} className="repo-form">
        <p><strong>{repository.full_name}</strong> · Nhánh mặc định: <code>{repository.default_branch}</code></p>
        <datalist id="recent-commits">{repository.commits.map(c => <option key={c.sha} value={c.sha}>{c.message}</option>)}</datalist>
        <div className="repo-commit-grid">
          <label>Commit gốc (base)<input required list="recent-commits" pattern="[a-f0-9]{40}" title="SHA commit đầy đủ, 40 ký tự" value={base} disabled={!!busy} onChange={e => { setBase(e.target.value); setResult(null) }} /></label>
          <label>Commit mới (target)<input required list="recent-commits" pattern="[a-f0-9]{40}" title="SHA commit đầy đủ, 40 ký tự" value={target} disabled={!!busy} onChange={e => chooseTarget(e.target.value)} /></label>
        </div>
        <button type="button" disabled={!!busy || !/^[a-f0-9]{40}$/.test(target)} onClick={() => { void run('tree') }}>Xem cây tại target commit</button>
        {tree && <RepositoryTreeView key={`${tree.repository_url}-${tree.commit}`} tree={tree} />}
        <details><summary>10 commit gần nhất để chọn</summary><ul>{repository.commits.map(c => <li key={c.sha}>
          <code>{c.sha.slice(0, 10)}</code> — {c.message}{' '}
          <button type="button" disabled={!!busy} onClick={() => { setBase(c.sha); setResult(null) }}>Chọn base</button>{' '}
          <button type="button" disabled={!!busy} onClick={() => chooseTarget(c.sha)}>Chọn target</button>
        </li>)}</ul></details>
        <label htmlFor="analysis-question">Bạn muốn tập trung vào điều gì?</label>
        <textarea id="analysis-question" maxLength={600} rows={2} value={question} disabled={!!busy} onChange={e => setQuestion(e.target.value)} />
        <label className="checkbox-row"><input type="checkbox" checked={useLlm} disabled={!!busy} onChange={e => setUseLlm(e.target.checked)} /> Dùng Gemini để giải thích bằng tiếng Việt</label>
        <p className="muted">Mặc định phân tích tĩnh. Gửi trích đoạn source code chưa được hỗ trợ trong đợt này; báo cáo đã lưu mở lại không dùng lượt Gemini.</p>
        {useLlm && <label className="checkbox-row"><input type="checkbox" checked={consent} required disabled={!!busy} onChange={e => setConsent(e.target.checked)} />
          Tôi đồng ý gửi tên file, symbol, commit, quan hệ import và câu hỏi đến Gemini. Hệ thống không tự gửi nội dung file; không nhập source riêng tư hoặc thông tin bí mật vào câu hỏi. Tối đa 0,02 USD/lượt, 5 lượt/phiên demo.
        </label>}
        <button type="submit" className="primary" disabled={!!busy || (useLlm && !consent)}>Phân tích thay đổi</button>
      </form>}
      {busy && <p role="status" aria-live="polite">{busy} Có thể mất khoảng 1–2 phút với repo mới.</p>}
      {error && <p role="alert" className="notice error">{error}</p>}
    </div>
    {result && <RepositoryResult key={result.report.report_id} result={result} saved={saved} exportedAt={exportedAt} headingRef={resultHeading} onDownload={download} />}
  </section>
}


export function RepositoryResult({ result, headingRef, onDownload, saved = false, exportedAt = null }: {
  result: Result; headingRef?: RefObject<HTMLHeadingElement | null>; onDownload: () => void; saved?: boolean; exportedAt?: string | null
}) {
  const [focusPath, setFocusPath] = useState('')
  const changes = result.report.stages.changes.data?.components ?? []
  const changedPaths = [...new Set(changes.map(c => c.path))]
  const ids = new Set(changes.filter(c => c.path === focusPath).map(c => c.id))
  const affected = (result.report.stages.impact.data?.candidates ?? []).filter(c => ids.has(c.changed_component_id))
  const evidenceDetails = useRef<HTMLDetailsElement>(null)
  function revealEvidence(id: string) {
    if (evidenceDetails.current) evidenceDetails.current.open = true
    document.getElementById(`metadata-${id}`)?.focus()
  }
  return <>
      <section className="card" aria-labelledby="analysis-result-title">
        <div className="section-heading"><h2 id="analysis-result-title" tabIndex={-1} ref={headingRef}>Kết quả: {result.repository.full_name}</h2><button type="button" onClick={onDownload}>Tải báo cáo JSON đầy đủ</button></div>
        {saved && <p className="notice"><strong>Báo cáo đã lưu</strong> · {exportedAt ? `Thời điểm xuất: ${exportedAt}` : 'Không có thông tin thời điểm'}. Mở lại không chạy phân tích hoặc gọi Gemini; thời điểm xuất không phải thời điểm phân tích.</p>}
        <p><strong>{result.report.data_kind === 'real' ? 'Dữ liệu phân tích repo' : 'DEMO — dữ liệu minh họa'}</strong> · {result.files.length} file tại target · {result.report.stages.changes.data ? changedPaths.length : 'chưa đo'} file thay đổi · {result.report.stages.impact.data?.candidates.length ?? 'chưa đo'} ứng viên ảnh hưởng</p>
        <div className="report-identity"><p>Repo: <code>{result.repository.repository_url}</code></p><p>Base: <code>{result.report.identity.base.commit}</code></p><p>Target: <code>{result.report.identity.target.commit}</code></p></div>
        <p className="muted">Ảnh hưởng tiềm năng theo phân tích tĩnh Python. Chưa chọn hoặc chạy regression test; số ứng viên có thể gồm nhiều thành phần trong cùng file.</p>
        <details><summary>Xem cấu trúc file tại target commit</summary><pre>{result.files.join('\n')}</pre></details>
        <label className="impact-filter" htmlFor="focus-changed-file">Xem ảnh hưởng tiềm năng từ file đã thay đổi
          <select id="focus-changed-file" value={focusPath} onChange={e => setFocusPath(e.target.value)}>
            <option value="">Chọn một file để xem ảnh hưởng</option>
            {changedPaths.map(path => <option key={path} value={path}>{path}</option>)}
          </select>
        </label>
        {focusPath && <div role="status">
          <p><code>{focusPath}</code>: {affected.length} ứng viên ảnh hưởng từ graph import tĩnh.</p>
          {affected.length ? <ul>{affected.map(c => <li key={c.id}><code>{c.path}</code>{c.symbol ? ` · ${c.symbol}` : ''} — {c.relationship === 'changed' ? 'thay đổi trực tiếp' : c.relationship === 'direct' ? 'phụ thuộc trực tiếp' : 'phụ thuộc gián tiếp'}</li>)}</ul>
            : <p>Chưa quan sát được đường ảnh hưởng trong graph hiện có; không có nghĩa file này an toàn hoặc không ảnh hưởng.</p>}
        </div>}
        <h3>Giải thích của Gemini</h3>
        {result.narrative.status === 'completed' && result.narrative.data ? <>
          <p className="muted">Nhận định từ metadata, cần đối chiếu bằng chứng bên dưới. Không xác nhận thay đổi hành vi hay kết quả test.</p>
          <p>{result.narrative.data.summary}</p>
          {result.narrative.data.findings.map((finding, i) => <article key={i} className="llm-finding">
            <strong><code>{finding.path}</code></strong><p>{finding.explanation}</p>
            <p className="metadata-links">Tham chiếu metadata: {finding.evidence_ids.map(id => <a key={id} href={`#metadata-${id}`} onClick={() => revealEvidence(id)}>{id}</a>)}</p>
          </article>)}
          <p className="muted">Model: {result.narrative.model ?? 'chưa ghi nhận'} · Token: {result.narrative.usage?.total_tokens ?? 'chưa đo'} · Chi phí thực tế: {result.narrative.usage?.cost_usd ?? 'chưa xác định'}</p>
          <ul>{result.narrative.data.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul>
        </> : <p className="notice">{result.narrative.status === 'not_run' ? 'Bạn đã chọn phân tích tĩnh, không gọi Gemini.' : messages[result.narrative.error_code ?? ''] ?? `Gemini chưa hoàn tất (${result.narrative.error_code ?? 'unknown'}). Kết quả tĩnh vẫn có bên dưới.`}</p>}
        <details ref={evidenceDetails}><summary>Đối chiếu các tham chiếu metadata của Gemini</summary><ul>{result.narrative_evidence.map(e => <li key={e.id} id={`metadata-${e.id}`} tabIndex={-1} className="metadata-item">
          <code>{e.id}</code> · <code>{e.path}</code> · {e.change ?? e.relationship ?? ''}{e.symbol ? ` · ${e.symbol}` : ''}{e.imports ? ` → imports ${e.imports}` : ''}
        </li>)}</ul></details>
        <details><summary>Phạm vi và giới hạn của kết quả</summary><ul>{result.limitations.map(l => <li key={l}>{l}</li>)}</ul></details>
      </section>
      <StageReportView report={result.report} />
    </>
}
