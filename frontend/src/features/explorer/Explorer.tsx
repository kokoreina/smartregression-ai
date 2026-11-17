import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ReactFlow, Background, Controls, MarkerType, type Node, type Edge } from '@xyflow/react'
import dagre from '@dagrejs/dagre'
import '@xyflow/react/dist/style.css'
import type { components } from '../../types/generated'
import { productRequest } from '../auth/authClient'
import { FormNotice } from '../auth/AuthViews'
import { RepositoryTreeView } from '../repositories/RepositoryTreeView'
import { treeValue } from '../repositories/repositoryTree'
import './explorer.css'
import { Notes } from './Notes'
import { ResumeState } from './ResumeState'
import { Assistance } from './Assistance'

type View = components['schemas']['GraphView']
type Tree = components['schemas']['RepositoryTree']
type Info = components['schemas']['SnapshotInfo']
type GraphNode = components['schemas']['ExplorerNode']
type Evidence = components['schemas']['GraphEvidence']
type Impact = components['schemas']['ImpactSummary']
type Source = components['schemas']['SourceRange']
type Hotspots = components['schemas']['Hotspots']
type CallPaths = components['schemas']['CallPaths']

function layout(view: View | null): { nodes: Node[]; edges: Edge[] } {
  if (!view) return { nodes: [], edges: [] }
  const graph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}))
  graph.setGraph({ rankdir: 'LR', nodesep: 30, ranksep: 80 })
  for (const node of view.nodes) graph.setNode(node.id, { width: 185, height: 58 })
  for (const edge of view.edges) graph.setEdge(edge.source, edge.target)
  dagre.layout(graph)
  const colors: Record<string, string> = { contains: '#77857e', imports: '#255c42', calls: '#7059a3' }
  return {
    nodes: view.nodes.map(node => ({ id: node.id, position: { x: graph.node(node.id).x - 92.5, y: graph.node(node.id).y - 29 }, data: { label: node.label }, ariaLabel: `${node.kind} ${node.path}${node.symbol ? ' ' + node.symbol : ''}`, style: { width: 185, minHeight: 58, borderRadius: 10, border: '1px solid #95b3a0', background: node.kind === 'directory' ? '#edf3e9' : '#fff', color: '#173b37' } })),
    edges: view.edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target, label: edge.kind, animated: false, style: { stroke: colors[edge.kind] }, markerEnd: { type: MarkerType.ArrowClosed, color: colors[edge.kind] } })),
  }
}

export function GraphPreview({ view, comparison, side }: { view: View; comparison?: View; side?: 'before' | 'after' }) {
  const graph = useMemo(() => layout(view), [view])
  const key = (node: View['nodes'][number]) => `${node.path}:${node.kind}:${node.symbol ?? ''}`
  const other = new Set(comparison?.nodes.map(key) ?? [])
  const changedIds = new Set(comparison ? view.nodes.filter(node => !other.has(key(node))).map(node => node.id) : [])
  return <section><p>{view.nodes.length}/{view.total_nodes} node · {view.edges.length}/{view.total_edges} cạnh trong phạm vi xem{view.truncated ? ' · đã giới hạn' : ''}</p>
    {comparison && <p>{side === 'before' ? 'Viền cam: thành phần bỏ so với B/target.' : 'Viền xanh: thành phần thêm so với A/base.'} So sánh trên phạm vi node đang hiển thị; tổng delta ở bảng chi tiết.</p>}
    <div className="graph-frame"><ReactFlow key={`${view.commit}-${view.nodes[0]?.id ?? ''}`} nodes={graph.nodes.map(node => changedIds.has(node.id) ? { ...node, className: 'graph-change-highlight', style: { ...node.style, border: `2px solid ${side === 'before' ? '#a75a21' : '#207346'}`, background: side === 'before' ? '#fff2e6' : '#e9f7eb' } } : node)} edges={graph.edges} fitView nodesDraggable={false} minZoom={0.15} maxZoom={2}><Background /><Controls /></ReactFlow></div></section>
}

function ExplorerWorkspace() {
  const { projectId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const commit = searchParams.get('commit') ?? ''
  const path = searchParams.get('path') ?? ''
  const [input, setInput] = useState(commit)
  const [view, setView] = useState<View | null>(null)
  const [tree, setTree] = useState<Tree | null>(null)
  const [info, setInfo] = useState<Info | null>(null)
  const [impact, setImpact] = useState<{ scope: string; data: Impact } | null>(null)
  const [hotspots, setHotspots] = useState<Hotspots | null>(null)
  const [source, setSource] = useState<Source | null>(null)
  const [evidence, setEvidence] = useState<Evidence | null>(null)
  const [callResult, setCalls] = useState<{ scope: string; data: CallPaths } | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [refresh, setRefresh] = useState(0)
  const [tab, setTab] = useState('graph')
  const [list, setList] = useState<GraphNode[]>([])
  const [offset, setOffset] = useState(0)
  const [focusOnly, setFocusOnly] = useState(false)
  const [showSource, setShowSource] = useState(false)
  const [expanded, setExpanded] = useState<string[]>([])
  const requestId = useRef(0)
  const navigationId = useRef(0)
  const interactionId = useRef(0)
  const flight = useRef(false)
  const mounted = useRef(false)
  const heading = useRef<HTMLHeadingElement>(null)
  const base = `/projects/${projectId}/snapshots/${commit}`
  const usable = /^[0-9a-f]{40}$/.test(commit)
  const currentEvidence = evidence?.commit === commit && evidence.path === path ? evidence : null
  useEffect(() => {
    mounted.current = true
    return () => { mounted.current = false; requestId.current += 1; interactionId.current += 1 }
  }, [])
  useEffect(() => { navigationId.current += 1 }, [base, path])
  const restore = useCallback((saved: components['schemas']['ViewState']) => {
    if (!searchParams.has('commit')) {
      setInput(saved.commit); setTab(saved.tab ?? 'graph'); setFocusOnly(saved.focus_only ?? false); setExpanded(saved.expanded_paths ?? [])
      setSearchParams({ commit: saved.commit, ...(saved.path ? { path: saved.path } : {}) }, { replace: true })
    }
  }, [searchParams, setSearchParams])
  const choose = useCallback((selected: string, proof?: Evidence | null) => {
    interactionId.current += 1
    setEvidence(proof ?? null); setShowSource(false); setSource(null); setCalls(null); setImpact(null)
    setSearchParams(previous => { const next = new URLSearchParams(previous); next.set('path', selected); return next })
    setTab('details')
  }, [setSearchParams])

  useEffect(() => {
    if (!usable) return
    let cancelled = false
    const id = ++requestId.current
    const active = () => !cancelled && id === requestId.current
    Promise.all([
      productRequest<View>(`${base}/graph${focusOnly && path ? '?focus=' + encodeURIComponent(path) : ''}`),
      productRequest<Tree>(`${base}/tree`), productRequest<Hotspots>(`${base}/hotspots`),
      productRequest<GraphNode[]>(`${base}/nodes?offset=${offset}`),
    ]).then(([graph, entries, hubs, nodes]) => { if (active()) { setView(graph); setTree(entries); setHotspots(hubs); setList(nodes) } })
      .catch(cause => { if (active()) setError(cause instanceof Error ? cause.message : 'Chưa đọc được snapshot. Hãy bấm tải snapshot.') })
    return () => { cancelled = true }
  }, [base, usable, refresh, focusOnly, path, offset])

  useEffect(() => {
    if (!usable || !path) return
    let cancelled = false
    productRequest<Impact>(`${base}/impact?path=${encodeURIComponent(path)}`)
      .then(value => { if (!cancelled) setImpact({ scope: `${base}:${path}`, data: value }) })
      .catch(() => { if (!cancelled) setImpact(null) })
    return () => { cancelled = true }
  }, [base, path, usable, refresh])

  async function materialize(event: React.FormEvent) {
    event.preventDefault()
    if (flight.current) return
    flight.current = true; setBusy(true); setError(''); setView(null); setTree(null); setImpact(null); setSource(null); setCalls(null); setEvidence(null); setOffset(0)
    interactionId.current += 1
    const generation = navigationId.current
    const requestedCommit = input
    const active = () => mounted.current && generation === navigationId.current
    try {
      const result = await productRequest<Info>(`/projects/${projectId}/snapshots`, 'POST', { commit: requestedCommit })
      if (active()) { setInfo(result); setSearchParams({ commit: requestedCommit }); setRefresh(value => value + 1); setTab('graph'); heading.current?.focus() }
    } catch (cause) { if (active()) setError(cause instanceof Error ? cause.message : 'Không phân tích được snapshot.') }
    finally { flight.current = false; if (mounted.current) setBusy(false) }
  }

  async function readSource() {
    setError('')
    const selectedPath = path; const selectedCommit = commit
    const generation = ++interactionId.current
    try {
      const start = currentEvidence?.line_start ?? 1
      const end = currentEvidence?.line_end ? Math.min(start + 199, currentEvidence.line_end) : 100
      const result = await productRequest<Source>(`${base}/source?path=${encodeURIComponent(path)}&start=${start}&end=${end}`)
      if (generation === interactionId.current && selectedPath === result.path && selectedCommit === result.commit) { setSource(result); setShowSource(true) }
    } catch (cause) { if (generation === interactionId.current) setError(cause instanceof Error ? cause.message : 'Đoạn source này không sẵn sàng.') }
  }

  async function readCalls(node: GraphNode) {
    setError(''); choose(node.path, node.evidence)
    const generation = interactionId.current
    try { const value = await productRequest<CallPaths>(`${base}/calls?node=${node.id}`); if (generation === interactionId.current) setCalls({ scope: `${base}:${node.path}`, data: value }) }
    catch (cause) { if (generation === interactionId.current) setError(cause instanceof Error ? cause.message : 'Không đọc được static call path.') }
  }

  const currentView = view?.commit === commit ? view : null
  const graph = useMemo(() => layout(currentView), [currentView])
  const selectedImpact = impact?.scope === `${base}:${path}` ? impact.data : null
  const calls = callResult?.scope === `${base}:${path}` ? callResult.data : null
  const currentTree = tree?.commit === commit ? tree : null
  const callNodes = new Map([...(currentView?.nodes ?? []), ...(calls?.nodes ?? [])].map(node => [node.id, node]))
  return <section className="explorer-page"><Link to={`/app/projects/${projectId}`}>← Về dự án</Link><p className="eyebrow">CẤU TRÚC VÀ QUAN HỆ PHỤ THUỘC</p><h1 ref={heading} tabIndex={-1}>Khám phá repository</h1>
    <form className="explorer-toolbar" onSubmit={materialize} aria-busy={busy}><label htmlFor="snapshot-sha">Commit SHA đầy đủ</label><input id="snapshot-sha" value={input} onChange={e => setInput(e.target.value)} pattern="[0-9a-f]{40}" required minLength={40} maxLength={40} disabled={busy} /><button className="primary-button" disabled={busy}>{busy ? 'Đang tải và phân tích…' : 'Tải snapshot và graph'}</button></form>
    <p className="field-hint">Phân tích tĩnh Python và JavaScript được hỗ trợ. Không cài dependency, chạy source hoặc gọi Gemini khi mở graph.</p>
    {error && <FormNotice error>{error}</FormNotice>}{!currentView && !busy && <FormNotice>Tải snapshot để xem graph. Liên kết đã lưu chỉ đọc cache; không tự tải lại từ GitHub.</FormNotice>}
    <ResumeState projectId={projectId ?? ''} value={{ commit, path: path || null, tab: tab === 'tree' ? 'tree' : tab === 'details' ? 'details' : 'graph', focus_only: focusOnly, expanded_paths: expanded }} ready={!!currentView} restore={restore} />
    {currentView && <><div className="graph-summary"><span>{currentView.nodes.length}/{currentView.total_nodes} node đang hiển thị</span><span>{currentView.coverage.analyzed_files.length} file đã phân tích</span><span>{currentView.coverage.status === 'complete' ? 'Trong phạm vi hỗ trợ' : 'Phạm vi phân tích chưa đầy đủ'}</span>{currentView.truncated && <strong>Graph đã giới hạn 150 node; dùng danh sách hoặc focus để xem tiếp.</strong>}</div>
      {info?.commit === commit && info.excluded_count > 0 && <p>{info.excluded_count} đường dẫn không được đọc/lưu source theo chính sách.</p>}
      <div className="explorer-tabs" role="group" aria-label="Vùng khám phá">{[['tree', 'Cây thư mục'], ['graph', 'Graph'], ['details', 'Chi tiết']].map(([value, label]) => <button type="button" key={value} aria-pressed={tab === value} onClick={() => setTab(value ?? 'graph')}>{label}</button>)}</div>
      <div className={`explorer-grid tab-${tab}`}><aside className="explorer-tree">{currentTree && <RepositoryTreeView tree={treeValue(currentTree, currentTree.repository_url, commit)} selectedPath={path} onSelect={selected => choose(selected)} expandedPaths={expanded} onExpand={(folder, open) => setExpanded(previous => open === previous.includes(folder) ? previous : open ? [...previous, folder].slice(0, 1000) : previous.filter(item => item !== folder))} />}</aside>
        <section className="explorer-canvas"><h2>Quan hệ tĩnh</h2><p className="graph-legend">contains: thư mục chứa thành phần · imports: file sử dụng → file được sử dụng · calls: caller → hàm được gọi</p>
          <label className="checkbox-label"><input type="checkbox" checked={focusOnly} onChange={e => setFocusOnly(e.target.checked)} />Focus vào file đã chọn</label>
          <div className="graph-frame"><ReactFlow key={`${commit}-${focusOnly}-${focusOnly ? path : ''}`} nodes={graph.nodes.map(node => ({ ...node, selected: currentView.nodes.find(item => item.id === node.id)?.path === path }))} edges={graph.edges} fitView minZoom={0.15} maxZoom={2} nodesDraggable={false} onNodeClick={(_, node) => { const value = currentView.nodes.find(item => item.id === node.id); if (value) choose(value.path, value.evidence) }} onEdgeClick={(_, edge) => { const value = currentView.edges.find(item => item.id === edge.id); if (value) choose(value.evidence.path, value.evidence) }}><Background /><Controls /></ReactFlow></div>
          <details><summary>Danh sách thay thế — dùng bàn phím</summary><ul className="graph-node-list">{list.map(node => <li key={node.id}><button type="button" onClick={() => choose(node.path, node.evidence)}>{node.path}{node.symbol ? ` · ${node.symbol}` : ''}</button>{node.kind !== 'directory' && <button type="button" onClick={() => void readCalls(node)}>Call paths</button>}</li>)}</ul><div className="dialog-actions"><button disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 100))}>Trước</button><button disabled={list.length < 100} onClick={() => setOffset(value => value + 100)}>Tiếp</button></div></details>
          <details><summary>Hotspots cấu trúc</summary>{hotspots?.cycles.length ? hotspots.cycles.map((cycle, index) => <p key={index}>Vòng phụ thuộc: {cycle.map(file => <button key={file} onClick={() => choose(file)}>{file}</button>)}</p>) : <p>Không quan sát thấy vòng trong graph đã phân tích.</p>}<ul>{Object.entries(hotspots?.fan_in ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([file, count]) => <li key={file}><button onClick={() => choose(file)}>{file}</button> · fan-in {count} · fan-out {hotspots?.fan_out[file]}</li>)}</ul><p>Chỉ số cấu trúc, chưa phải lỗi hoặc điểm rủi ro.</p></details>
        </section><aside className="explorer-inspector"><h2>Chi tiết và ảnh hưởng</h2>{path ? <><code className="selected-path">{path}</code><p>Commit: {commit.slice(0, 12)}</p>{currentEvidence && <p>{currentEvidence.kind === "metadata" ? "Bằng chứng metadata của file/thư mục" : `Bằng chứng dòng ${currentEvidence.line_start}–${currentEvidence.line_end}`}</p>}<button onClick={() => void readSource()}>Xem đoạn mã nguồn</button>
          {showSource && source?.path === path && source.commit === commit && <pre className="source-range"><code>{source.content}</code></pre>}
          {selectedImpact && <div className="impact-metrics"><h3>Ảnh hưởng tiềm năng theo phân tích tĩnh</h3>{[['changed', 'Thay đổi'], ['direct', 'Trực tiếp'], ['indirect', 'Gián tiếp']].map(([key, label]) => <div className="impact-stat" key={key}><span>{label}</span><strong>{selectedImpact.counts[key ?? ''] ?? 0}/{selectedImpact.denominator ?? 'N/A'} file · {selectedImpact.percentages[key ?? ''] == null ? 'N/A' : `${selectedImpact.percentages[key ?? '']}%`}</strong></div>)}<p>Mẫu số: file phân tích được trong snapshot. Tỷ lệ không phải xác suất gây lỗi.</p><p>{selectedImpact.unresolved_count} quan hệ chưa giải được; {selectedImpact.coverage.unsupported_files.length} file ngoài phạm vi.</p><h4>Trực tiếp</h4>{selectedImpact.direct.map(file => <button key={file} onClick={() => choose(file)}>{file}</button>)}<h4>Gián tiếp</h4>{selectedImpact.indirect.map(file => <button key={file} onClick={() => choose(file)}>{file}</button>)}</div>}
          {calls && <div><h3>Static call paths — chưa phải runtime trace</h3>{calls.paths.map((items, index) => <p key={index}>{items.map((id, step) => { const node = callNodes.get(id); return <span key={`${id}-${step}`}>{step > 0 && ' → '}<button type="button" disabled={!node} onClick={() => node && choose(node.path, node.evidence)}>{node?.symbol ?? node?.path ?? id.slice(0, 10)}</button></span> })}</p>)}{calls.truncated && <p>Đã dừng ở giới hạn duyệt.</p>}<p>{calls.unresolved.length} điểm chưa giải được trong các file liên quan.</p><ul>{calls.unresolved.slice(0, 50).map((item, index) => <li key={index}><button type="button" onClick={() => choose(item.path)}>{item.path}:{item.line}</button> · {item.reason}{item.reference ? ` · ${item.reference}` : ''}</li>)}</ul>{calls.unresolved.length > 50 && <p>Đang liệt kê 50 điểm đầu; số tổng phía trên vẫn giữ nguyên.</p>}</div>}
          <p><Link className="text-link" to={`/app/projects/${projectId}/what-if?commit=${commit}&path=${encodeURIComponent(path)}`}>Thử thay đổi file này →</Link></p>
          <Notes key={commit} projectId={projectId ?? ''} commit={commit} path={path} />
        </> : <p>Chọn file, symbol hoặc cạnh để đối chiếu bằng chứng.</p>}</aside>
      </div><Assistance key={base} base={base} path={path} choose={choose} /></>}
  </section>
}

export function Explorer() {
  const { projectId } = useParams()
  return <ExplorerWorkspace key={projectId} />
}
