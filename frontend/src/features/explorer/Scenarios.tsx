import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import type { components } from '../../types/generated'
import { productRequest, productDownload } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'
import { GraphPreview } from './Explorer'
import { SnapshotAi } from './SnapshotAi'

type Scenario = components['schemas']['ScenarioView']
type Page = components['schemas']['ScenarioViewPage']
type Comparison = components['schemas']['ScenarioComparison']
type Delta = components['schemas']['GraphDelta']
type Graph = components['schemas']['GraphView']

function DeltaView({ value }: { value: Delta }) {
  return <section className="auth-card activity-card"><h3>Thay đổi cấu trúc graph</h3><p>Base {value.base_commit.slice(0, 12)} → Target {value.target_commit.slice(0, 12)}</p>
    <p>Node: +{value.total_added_nodes} / −{value.total_removed_nodes} / {value.retained_node_count} giữ lại. Edge: +{value.total_added_edges} / −{value.total_removed_edges} / {value.retained_edge_count} giữ lại.</p>
    {value.truncated && <FormNotice>Danh sách đã giới hạn; tổng số phía trên tính trên toàn scope phân tích.</FormNotice>}
    <h4>Thêm</h4><ul>{value.added_nodes.map(node => <li key={node.id}>{node.path}{node.symbol ? ` · ${node.symbol}` : ''}{node.evidence?.source_kind === 'overlay' ? ' · overlay giả lập' : ''}</li>)}</ul>
    <h4>Bỏ</h4><ul>{value.removed_nodes.map(node => <li key={node.id}>{node.path}{node.symbol ? ` · ${node.symbol}` : ''} · bằng chứng base</li>)}</ul>
    <ul>{value.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul>
  </section>
}

export function ScenarioResult({ value }: { value: Scenario }) {
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)
  async function download() {
    if (downloading) return
    setDownloading(true); setError('')
    try {
      const blob = await productDownload(`/projects/${value.project_id}/scenarios/${value.id}/export`)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = `smartregression-scenario-${value.id}.json`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Không xuất được scenario.') }
    finally { setDownloading(false) }
  }
  return <section className="auth-card activity-card"><h2>{value.title}</h2><p>{value.analysis_kind === 'hypothesis' ? 'GIẢ THUYẾT — chưa phải code đã thay đổi' : 'OVERLAY TĨNH — chưa commit hoặc chạy source'}</p><p className="repository-url">{value.path} · Baseline {value.baseline}</p>
    <p>Scenario {value.id} · {new Date(value.created_at).toLocaleString('vi-VN')}</p>
    {value.analysis_kind === 'static_overlay' && <><p>Symbol mới: {value.added_symbols.length ? value.added_symbols.join(', ') : 'Không quan sát thấy'}</p><p>Symbol bỏ: {value.removed_symbols.length ? value.removed_symbols.join(', ') : 'Không quan sát thấy'}</p>
      <p>Graph: +{value.added_node_count ?? 'chưa đo'} node, −{value.removed_node_count ?? 'chưa đo'} node; +{value.added_edge_count ?? 'chưa đo'} edge, −{value.removed_edge_count ?? 'chưa đo'} edge.</p></>}
    {value.impact && <><h3>Ảnh hưởng tiềm năng trong overlay</h3><p>{value.impact.direct.length} file trực tiếp · {value.impact.indirect.length} file gián tiếp · mẫu số {value.impact.denominator ?? 'N/A'} file phân tích được.</p><p>Phạm vi tiềm năng: {value.impact.percentages.potential == null ? 'N/A' : `${value.impact.percentages.potential}%`} — không phải xác suất gây lỗi.</p>
      <ul>{[...value.impact.direct, ...value.impact.indirect].map(file => <li key={file}>{file}</li>)}</ul><p>{value.impact.unresolved_count} quan hệ chưa giải được.</p></>}
    {value.analysis_kind === 'hypothesis' && <><p>Không tính % ảnh hưởng từ mô tả tự nhiên. Nội dung được lưu để đối chiếu; chưa tự gửi Gemini.</p><SnapshotAi key={value.id} projectId={value.project_id} commit={value.baseline} path={value.path} scenarioId={value.id} /></>}
    <ul>{value.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul>{error && <FormNotice error>{error}</FormNotice>}<button disabled={downloading} onClick={() => void download()}>Xuất scenario JSON đầy đủ</button>
    <Link to={`/app/projects/${value.project_id}/explorer?commit=${value.baseline}&path=${encodeURIComponent(value.path)}`}>Đối chiếu source/graph tại baseline →</Link>
  </section>
}

export function WhatIf() {
  const { projectId } = useParams()
  const [params] = useSearchParams()
  const [baseline, setBaseline] = useState(params.get('commit') ?? '')
  const [path, setPath] = useState(params.get('path') ?? '')
  const [title, setTitle] = useState('Phương án thay đổi mới')
  const [mode, setMode] = useState<'code' | 'diff' | 'description'>('description')
  const [input, setInput] = useState('')
  const [result, setResult] = useState<Scenario | null>(null)
  const [items, setItems] = useState<Scenario[]>([])
  const [cursor, setCursor] = useState<string | null>(null)
  const [left, setLeft] = useState('')
  const [right, setRight] = useState('')
  const [comparison, setComparison] = useState<Comparison | null>(null)
  const [versionBase, setVersionBase] = useState('')
  const [versionTarget, setVersionTarget] = useState('')
  const [delta, setDelta] = useState<Delta | null>(null)
  const [graphs, setGraphs] = useState<{ labelA: string; labelB: string; a: Graph; b: Graph } | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const flight = useRef(false)
  const attempt = useRef<{ digest: string; key: string } | null>(null)
  useEffect(() => {
    let active = true
    productRequest<Page>(`/projects/${projectId}/scenarios`).then(value => { if (active) { setItems(value.items); setCursor(value.next_cursor ?? null) } }).catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Không đọc được scenario.') })
    return () => { active = false }
  }, [projectId])

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError('')
    const fingerprint = JSON.stringify({ baseline, path, title, mode, input })
    if (!attempt.current || attempt.current.digest !== fingerprint) attempt.current = { digest: fingerprint, key: crypto.randomUUID() }
    try {
      const value = await productRequest<Scenario>(`/projects/${projectId}/scenarios`, 'POST', { baseline, path, title, mode, input, idempotency_key: attempt.current.key })
      setResult(value); setItems(old => [value, ...old.filter(item => item.id !== value.id)])
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Không tạo được scenario.') }
    finally { flight.current = false; setBusy(false) }
  }

  async function compare(event: React.FormEvent, versions = false) {
    event.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError(''); setGraphs(null)
    try {
      if (versions) {
        setDelta(await productRequest<Delta>(`/projects/${projectId}/graph-comparisons`, 'POST', { base: versionBase, target: versionTarget }))
        const [a, b] = await Promise.all([productRequest<Graph>(`/projects/${projectId}/snapshots/${versionBase}/graph`), productRequest<Graph>(`/projects/${projectId}/snapshots/${versionTarget}/graph`)])
        setGraphs({ labelA: `Base ${versionBase}`, labelB: `Target ${versionTarget}`, a, b })
      } else {
        const value = await productRequest<Comparison>(`/projects/${projectId}/scenario-comparisons`, 'POST', { left, right }); setComparison(value)
        if (value.comparison_kind !== 'hypotheses') {
          const [a, b] = await Promise.all([productRequest<Graph>(`/projects/${projectId}/scenarios/${left}/graph`), productRequest<Graph>(`/projects/${projectId}/scenarios/${right}/graph`)])
          setGraphs({ labelA: `Scenario A ${left}`, labelB: `Scenario B ${right}`, a, b })
        }
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Không so sánh được. Cần cùng baseline/config và loại phân tích.') }
    finally { flight.current = false; setBusy(false) }
  }

  async function more() {
    if (!cursor || flight.current) return
    flight.current = true; setBusy(true)
    try { const value = await productRequest<Page>(`/projects/${projectId}/scenarios?cursor=${encodeURIComponent(cursor)}`); setItems(old => [...old, ...value.items]); setCursor(value.next_cursor ?? null) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Không tải được lịch sử scenario.') }
    finally { flight.current = false; setBusy(false) }
  }

  return <section><Link to={`/app/projects/${projectId}`}>← Về dự án</Link><p className="eyebrow">THỬ THAY ĐỔI MÀ KHÔNG SỬA REPO</p><h1>What-if và so sánh phương án</h1><p>Chọn một file đã có trong snapshot Explorer. Mô tả tự nhiên là giả thuyết; code/diff tạo overlay bất biến.</p>
    {error && <FormNotice error>{error}</FormNotice>}
    <form className="auth-card project-create" onSubmit={submit} aria-busy={busy}><label htmlFor="scenario-title">Tên phương án</label><input id="scenario-title" value={title} onChange={e => setTitle(e.target.value)} required maxLength={120} disabled={busy} />
      <label htmlFor="scenario-base">Baseline SHA</label><input id="scenario-base" value={baseline} onChange={e => setBaseline(e.target.value)} pattern="[0-9a-f]{40}" required minLength={40} maxLength={40} disabled={busy} />
      <label htmlFor="scenario-path">Đường dẫn file</label><input id="scenario-path" value={path} onChange={e => setPath(e.target.value)} required maxLength={2048} placeholder="src/payment.js" disabled={busy} />
      <label htmlFor="scenario-mode">Loại đầu vào</label><select id="scenario-mode" value={mode} disabled={busy} onChange={e => setMode(e.target.value === 'code' ? 'code' : e.target.value === 'diff' ? 'diff' : 'description')}><option value="description">Mô tả thay đổi — giả thuyết</option><option value="code">Nội dung mới của một file</option><option value="diff">Unified diff của một file</option></select>
      <label htmlFor="scenario-input">{mode === 'description' ? 'Mô tả thay đổi dự kiến' : mode === 'code' ? 'Toàn bộ nội dung file sau thay đổi' : 'Unified diff khớp baseline'}</label><textarea id="scenario-input" rows={12} value={input} onChange={e => setInput(e.target.value)} required maxLength={mode === 'description' ? 2000 : 262144} disabled={busy} />
      <p className="field-hint">Không chạy code, commit hoặc gọi AI khi lưu. Giới hạn code/diff 256 KiB; không nhập secrets. Bản nháp không tự lưu.</p><button className="primary-button" disabled={busy}>{busy ? 'Đang kiểm tra và lưu…' : 'Lưu và phân tích phương án'}</button></form>
    {result && <ScenarioResult value={result} />}
    {graphs && <div className="comparison-graphs"><section className="auth-card activity-card"><h3>{graphs.labelA}</h3><GraphPreview view={graphs.a} comparison={graphs.b} side="before" /></section><section className="auth-card activity-card"><h3>{graphs.labelB}</h3><GraphPreview view={graphs.b} comparison={graphs.a} side="after" /></section></div>}
    <section className="auth-card activity-card"><h2>Scenario đã lưu</h2>{items.length ? <ul>{items.map(item => <li key={item.id}><Link to={`/app/projects/${projectId}/scenarios/${item.id}`}>{item.title}</Link><span>{item.analysis_kind === 'hypothesis' ? 'Giả thuyết' : 'Overlay'} · {item.baseline.slice(0, 8)}</span></li>)}</ul> : <p>Chưa có phương án được lưu.</p>}{cursor && <button disabled={busy} onClick={() => void more()}>Tải thêm scenario</button>}</section>
    <form className="auth-card project-create" onSubmit={compare}><h2>So sánh A/B</h2><p>Chỉ cùng repo, baseline, cấu hình và loại phân tích. Số file ít hơn không đồng nghĩa an toàn hơn.</p>
      <label htmlFor="scenario-a">Phương án A</label><select id="scenario-a" value={left} onChange={e => setLeft(e.target.value)} required disabled={busy}><option value="">Chọn A</option>{items.map(item => <option value={item.id} key={item.id}>{item.title} · {item.baseline.slice(0, 8)}</option>)}</select>
      <label htmlFor="scenario-b">Phương án B</label><select id="scenario-b" value={right} onChange={e => setRight(e.target.value)} required disabled={busy}><option value="">Chọn B</option>{items.map(item => <option value={item.id} key={item.id}>{item.title} · {item.baseline.slice(0, 8)}</option>)}</select><button disabled={busy}>So sánh hai phương án</button></form>
    {comparison && <section className="auth-card activity-card"><h2>Kết quả A/B đã tính</h2><p>A {comparison.left} → B {comparison.right} · baseline {comparison.baseline.slice(0, 12)}</p>{comparison.comparison_kind === 'hypotheses' ? <p>Hai mô tả là giả thuyết. Chưa có static delta hoặc phần trăm; không xếp hạng an toàn.</p> : <><p>Ảnh hưởng thêm: {comparison.added_affected.length} · bớt: {comparison.removed_affected.length} · giữ nguyên: {comparison.retained_affected.length}.</p><p>Unresolved A: {comparison.unresolved_left ?? 'chưa đo'} · B: {comparison.unresolved_right ?? 'chưa đo'}.</p>{comparison.graph_delta && <DeltaView value={comparison.graph_delta} />}</>}</section>}
    <form className="auth-card project-create" onSubmit={event => void compare(event, true)}><h2>Graph qua hai phiên bản Git</h2><p>Hai snapshot cần được tải trong Explorer trước khi so sánh.</p><label htmlFor="graph-base">Base commit</label><input id="graph-base" value={versionBase} onChange={e => setVersionBase(e.target.value)} required pattern="[0-9a-f]{40}" maxLength={40} disabled={busy} /><label htmlFor="graph-target">Target commit</label><input id="graph-target" value={versionTarget} onChange={e => setVersionTarget(e.target.value)} required pattern="[0-9a-f]{40}" maxLength={40} disabled={busy} /><button disabled={busy}>So sánh graph phiên bản</button></form>{delta && <DeltaView value={delta} />}
  </section>
}

export function SavedScenario() {
  const { projectId, scenarioId } = useParams()
  const [value, setValue] = useState<Scenario | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    productRequest<Scenario>(`/projects/${projectId}/scenarios/${scenarioId}`).then(result => { if (active) setValue(result) }).catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Không đọc được scenario.') })
    return () => { active = false }
  }, [projectId, scenarioId])
  return <section><Link to={`/app/projects/${projectId}/what-if`}>← What-if và A/B</Link><h1>Phương án đã lưu</h1>{error && <FormNotice error>{error}</FormNotice>}{value && value.id === scenarioId ? <ScenarioResult value={value} /> : !error && <p role="status">Đang đọc phương án…</p>}</section>
}
