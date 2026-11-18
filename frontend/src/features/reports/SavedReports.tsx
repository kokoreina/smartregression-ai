import { useRef, useState } from 'react'
import { RepositoryResult } from '../repositories/RepositoryAnalysis'
import { loadRepositoryReport, type LoadedRepositoryReport } from '../repositories/repositoryReport'
import { loadStageReportFromFile } from './stageReport'
import { StageReportView } from './StageReportView'
import type { components } from '../../types/generated'
import { FormNotice } from '../auth/AuthViews'
import { WorkspaceIcon } from '../../components/WorkspaceIcon'
import './savedReports.css'

type Stage = components['schemas']['StageAnalysisReport']
type PortableScenario = { title: string; path: string; baseline: string; mode: string; created_at: string; description: string; direct: string[]; indirect: string[]; limitations: string[]; ai: { summary: string; findings: { path: string; explanation: string; ids: string[] }[] }[] }

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Định dạng object không hợp lệ.')
  return value as Record<string, unknown>
}
function text(value: unknown, max = 10000): string { if (typeof value !== 'string' || value.length > max) throw new Error('Trường văn bản không hợp lệ.'); return value }
function texts(value: unknown, max = 10000): string[] { if (!Array.isArray(value) || value.length > max) throw new Error('Danh sách không hợp lệ.'); return value.map(item => text(item, 4096)) }
function scenario(value: unknown): PortableScenario {
  const root = object(value)
  if (root.report_kind !== 'saved-scenario' || root.schema_version !== '1.0.0' || !Array.isArray(root.ai_requests) || root.ai_requests.length > 100) throw new Error('Phiên bản scenario chưa được hỗ trợ.')
  if (!Number.isFinite(Date.parse(text(root.exported_at, 80)))) throw new Error('Thời điểm xuất không hợp lệ.')
  const payload = object(root.payload)
  const sha = text(payload.baseline, 40)
  if (!/^[0-9a-f]{40}$/.test(sha) || payload.schema_version !== '1.0.0' || !['code', 'diff', 'description'].includes(text(payload.mode, 20))) throw new Error('Định danh scenario không hợp lệ.')
  const impact = payload.impact == null ? null : object(payload.impact)
  if (payload.mode === 'description' && (impact || payload.graph != null || payload.delta != null)) throw new Error('Giả thuyết không được chứa số liệu static.')
  const path = text(payload.path, 2048)
  if (path.startsWith('/') || path.includes('\\') || path.split('/').some(part => !part || part === '..' || part === '.')) throw new Error('Đường dẫn không hợp lệ.')
  const ai = root.ai_requests.flatMap(value => {
    const job = object(value)
    if (job.result == null) return []
    const result = object(job.result)
    if (result.status !== 'completed') return []
    const provenance = object(job.provenance)
    if (provenance.commit !== sha || provenance.scenario_id !== payload.id || !Array.isArray(provenance.observations)) throw new Error('AI không khớp scenario.')
    const observations = new Map(provenance.observations.map(value => { const proof = object(value); if (proof.commit !== sha) throw new Error('Bằng chứng sai SHA.'); return [text(proof.id, 80), text(proof.path, 2048)] }))
    const data = object(result.data)
    if (!Array.isArray(data.findings) || data.findings.length > 8) throw new Error('Giải thích không hợp lệ.')
    return [{ summary: text(data.summary), findings: data.findings.map(value => { const finding = object(value); const path = text(finding.path, 2048); const ids = texts(finding.evidence_ids, 180); if (!ids.length || ids.some(id => observations.get(id) !== path)) throw new Error('Citation không hợp lệ.'); return { path, explanation: text(finding.explanation), ids } }) }]
  })
  return { title: text(payload.title, 120), path, baseline: sha, mode: text(payload.mode, 20), created_at: text(payload.created_at, 80), description: text(payload.input, 262144), direct: impact ? texts(impact.direct) : [], indirect: impact ? texts(impact.indirect) : [], limitations: texts(payload.limitations, 100), ai }
}

export function SavedReports() {
  const [repository, setRepository] = useState<LoadedRepositoryReport | null>(null)
  const [stage, setStage] = useState<Stage | null>(null)
  const [savedScenario, setScenario] = useState<PortableScenario | null>(null)
  const [raw, setRaw] = useState('')
  const [filename, setFilename] = useState('report.json')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const dragDepth = useRef(0)
  const picker = useRef<HTMLInputElement>(null)
  const sequence = useRef(0)
  const hasReport = !!(repository || stage || savedScenario)
  const reportType = savedScenario ? 'Kịch bản thay đổi' : stage ? 'Báo cáo phân tích theo giai đoạn' : 'Báo cáo repository'
  function download() {
    const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }))
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  async function open(file: File) {
    const id = ++sequence.current
    setError(''); setLoading(true); setRepository(null); setStage(null); setScenario(null); setRaw('')
    try {
      if (file.size > 16 * 1024 * 1024) throw new Error('Báo cáo vượt giới hạn 16 MiB.')
      const content = await file.text()
      const value: unknown = JSON.parse(content)
      const kind = object(value).report_kind
      let repo = null; let canonical = null; let proposed = null
      if (kind === 'saved-scenario') proposed = scenario(value)
      else if (object(value).schema_version === '2.0.0' && !kind) canonical = await loadStageReportFromFile(file)
      else repo = await loadRepositoryReport(file)
      if (id !== sequence.current) return
      setRepository(repo); setStage(canonical); setScenario(proposed); setRaw(content); setFilename(file.name)
    } catch (cause) { if (id === sequence.current) setError(cause instanceof SyntaxError ? 'Không đọc được file JSON hợp lệ.' : cause instanceof Error ? cause.message : 'Không mở được JSON.') }
    finally { if (id === sequence.current) setLoading(false) }
  }
  function drop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault(); dragDepth.current = 0; setDragging(false)
    if (loading) return
    const files = event.dataTransfer.files
    if (files.length !== 1) { setError('Mỗi lần chỉ mở một file báo cáo.'); return }
    if (files[0]) void open(files[0])
  }
  return <section className="saved-reports-page" aria-labelledby="saved-reports-title"><div className="reports-heading"><div><h1 id="saved-reports-title">Báo cáo đã lưu</h1><p>Mở và đọc lại kết quả phân tích từ file JSON trên máy.</p></div><span className="reports-local-label">File trên máy</span></div>
    <input ref={picker} hidden type="file" aria-label="Chọn báo cáo JSON" accept=".json,application/json" onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; if (file) void open(file) }} />
    {!hasReport && <div className="report-import-panel" aria-busy={loading}><div className={`report-import-main${dragging ? ' is-dragging' : ''}`} role="region" aria-label="Vùng mở báo cáo" onDrop={drop} onDragOver={event => { if (event.dataTransfer.types.includes('Files')) { event.preventDefault(); event.dataTransfer.dropEffect = 'copy' } }} onDragEnter={event => { if (event.dataTransfer.types.includes('Files')) { event.preventDefault(); dragDepth.current += 1; setDragging(true) } }} onDragLeave={event => { if (event.dataTransfer.types.includes('Files')) { dragDepth.current = Math.max(0, dragDepth.current - 1); if (!dragDepth.current) setDragging(false) } }}><span className="report-file-symbol"><WorkspaceIcon name="reports" /></span><h2>{loading ? 'Đang đọc báo cáo…' : dragging ? 'Thả file để mở' : 'Kéo thả file JSON'}</h2><p>Xem lại kết quả, bằng chứng và phạm vi phân tích đã xuất từ SmartRegression.</p><button className="primary-button" disabled={loading} onClick={() => picker.current?.click()}>{loading ? 'Đang kiểm tra file…' : 'Chọn file JSON'}</button><span className="report-size-hint">Một file .json · Tối đa 16 MiB</span>{loading && <p role="status">Đang kiểm tra cấu trúc và phiên bản báo cáo.</p>}</div>
      <div className="report-format-guide"><h3>Các loại báo cáo hỗ trợ</h3><dl><div><dt>Phân tích repository</dt><dd>So sánh commit, file thay đổi và kết quả phân tích.</dd></div><div><dt>Phân tích theo giai đoạn</dt><dd>Trạng thái xử lý, ảnh hưởng và bằng chứng.</dd></div><div><dt>Kịch bản thay đổi</dt><dd>Giả thuyết hoặc kết quả overlay tĩnh đã lưu.</dd></div></dl></div></div>}
    {error && <FormNotice error>{error} Hãy chọn lại một báo cáo JSON được hỗ trợ.</FormNotice>}
    {!hasReport && <p className="report-import-note">File được đọc trong trình duyệt, không gọi GitHub hoặc Gemini. Nội dung import chưa được server xác thực.</p>}
    {hasReport && <><div className="report-open-toolbar"><div className="report-open-identity"><WorkspaceIcon name="reports" /><div><strong>{filename}</strong><span>{reportType} · Nguồn: file trên máy</span></div></div><div className="report-open-actions"><button onClick={() => picker.current?.click()}>Mở file khác</button><button onClick={download}>Tải JSON gốc</button><button onClick={() => window.print()}>In / Lưu PDF</button></div></div><p className="report-import-note">Thời điểm xuất khác thời điểm phân tích. File import chưa được server xác thực.</p><div className="saved-report-content">
    {repository && <RepositoryResult result={repository.result} saved exportedAt={repository.exportedAt} onDownload={download} />}
    {stage && <StageReportView report={stage} />}
    {savedScenario && <section className="auth-card"><h2>{savedScenario.title}</h2><p>{savedScenario.mode === 'description' ? 'GIẢ THUYẾT' : 'OVERLAY TĨNH'} · chưa chạy source</p><p>{savedScenario.path} · {savedScenario.baseline}</p><p>Tạo scenario: {savedScenario.created_at}</p><details><summary>Đầu vào đã lưu</summary><pre className="source-range">{savedScenario.description}</pre></details><h3>Ảnh hưởng tiềm năng</h3>{savedScenario.mode === 'description' ? <p>Chưa có số liệu static.</p> : <><p>Trực tiếp: {savedScenario.direct.join(', ') || 'Không quan sát thấy'}</p><p>Gián tiếp: {savedScenario.indirect.join(', ') || 'Không quan sát thấy'}</p></>}<ul>{savedScenario.limitations.map(item => <li key={item}>{item}</li>)}</ul>{savedScenario.ai.map((item, index) => <article key={index}><h3>Gemini đã lưu</h3><p>{item.summary}</p>{item.findings.map((finding, i) => <p key={i}><strong>{finding.path}</strong>: {finding.explanation}<br />Bằng chứng: {finding.ids.join(', ')}</p>)}</article>)}</section>}
    </div></>}
  </section>
}
