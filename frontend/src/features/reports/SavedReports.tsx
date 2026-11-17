import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { RepositoryResult } from '../repositories/RepositoryAnalysis'
import { loadRepositoryReport, type LoadedRepositoryReport } from '../repositories/repositoryReport'
import { loadStageReportFromFile } from './stageReport'
import { StageReportView } from './StageReportView'
import type { components } from '../../types/generated'
import { FormNotice } from '../auth/AuthViews'

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
  const sequence = useRef(0)
  function download() {
    const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }))
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  async function open(file: File) {
    const id = ++sequence.current
    setError('')
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
    } catch (cause) { if (id === sequence.current) setError(cause instanceof Error ? cause.message : 'Không mở được JSON.') }
  }
  return <main id="main-content" className="workspace-main"><Link to="/app">← Về ứng dụng</Link><h1>Mở báo cáo đã lưu</h1><p>Đọc file trên máy, không gọi GitHub hoặc Gemini. File import là dữ liệu do người dùng cung cấp, chưa được server xác thực.</p><label>Chọn báo cáo JSON<input type="file" accept=".json,application/json" onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; if (file) void open(file) }} /></label>{error && <FormNotice error>{error}</FormNotice>}
    {(repository || stage || savedScenario) && <><p className="notice">Báo cáo đã lưu · nguồn: file local. Thời điểm xuất khác thời điểm phân tích.</p><div className="dialog-actions"><button onClick={download}>Tải lại JSON gốc</button><button onClick={() => window.print()}>In / Lưu PDF</button></div></>}
    {repository && <RepositoryResult result={repository.result} saved exportedAt={repository.exportedAt} onDownload={download} />}
    {stage && <StageReportView report={stage} />}
    {savedScenario && <section className="auth-card"><h2>{savedScenario.title}</h2><p>{savedScenario.mode === 'description' ? 'GIẢ THUYẾT' : 'OVERLAY TĨNH'} · chưa chạy source</p><p>{savedScenario.path} · {savedScenario.baseline}</p><p>Tạo scenario: {savedScenario.created_at}</p><details><summary>Đầu vào đã lưu</summary><pre className="source-range">{savedScenario.description}</pre></details><h3>Ảnh hưởng tiềm năng</h3>{savedScenario.mode === 'description' ? <p>Chưa có số liệu static.</p> : <><p>Trực tiếp: {savedScenario.direct.join(', ') || 'Không quan sát thấy'}</p><p>Gián tiếp: {savedScenario.indirect.join(', ') || 'Không quan sát thấy'}</p></>}<ul>{savedScenario.limitations.map(item => <li key={item}>{item}</li>)}</ul>{savedScenario.ai.map((item, index) => <article key={index}><h3>Gemini đã lưu</h3><p>{item.summary}</p>{item.findings.map((finding, i) => <p key={i}><strong>{finding.path}</strong>: {finding.explanation}<br />Bằng chứng: {finding.ids.join(', ')}</p>)}</article>)}</section>}
  </main>
}
