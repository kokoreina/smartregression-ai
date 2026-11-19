import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ReactFlow, Background, Controls, MarkerType, Position, type Node, type Edge, type ReactFlowInstance } from '@xyflow/react'
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
import { ImpactOverview } from './ImpactOverview'
import { CoverageDetails } from './CoverageDetails'

type View = components['schemas']['GraphView']
type Tree = components['schemas']['RepositoryTree']
type Info = components['schemas']['SnapshotInfo']
type GraphNode = components['schemas']['ExplorerNode']
type Evidence = components['schemas']['GraphEvidence']
type Impact = components['schemas']['ImpactSummary']
type Source = components['schemas']['SourceRange']
type Hotspots = components['schemas']['Hotspots']
type CallPaths = components['schemas']['CallPaths']

function layout(view: View | null, showLabels = true): { nodes: Node[]; edges: Edge[] } {
  if (!view) return { nodes: [], edges: [] }
  const graph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}))
  graph.setGraph({ rankdir: 'LR', nodesep: 42, ranksep: 110 })
  for (const node of view.nodes) graph.setNode(node.id, { width: 220, height: 76 })
  for (const edge of view.edges) graph.setEdge(edge.source, edge.target)
  dagre.layout(graph)
  const colors: Record<string, string> = { contains: 'var(--graph-contains)', imports: 'var(--graph-imports)', calls: 'var(--graph-calls)' }
  const kinds: Record<string, string> = { file: 'File', directory: 'Thư mục', function: 'Hàm', class: 'Lớp' }
  const paths = new Map(view.nodes.map(node => [node.id, node.path]))
  return {
    nodes: view.nodes.map(node => ({
      id: node.id, position: { x: graph.node(node.id).x - 110, y: graph.node(node.id).y - 38 }, sourcePosition: Position.Right, targetPosition: Position.Left,
      data: { kind: node.kind, label: <div className="repository-graph-node"><span>{kinds[node.kind] ?? node.kind}</span><strong title={node.label}>{node.label}</strong><small title={node.path}>{node.path.includes('/') ? node.path.slice(0, node.path.lastIndexOf('/')) : './'}</small></div> },
      ariaLabel: `${node.kind} ${node.path}${node.symbol ? ' ' + node.symbol : ''}`,
      style: { width: 220, minHeight: 76, borderRadius: 10, padding: '10px 14px', border: '1px solid var(--border-strong)', background: 'var(--graph-node)', color: 'var(--foreground)' },
    })),
    edges: view.edges.map(edge => ({ id: edge.id, source: edge.source, target: edge.target, label: showLabels ? edge.kind : undefined, ariaLabel: `${edge.kind}: ${paths.get(edge.source)} → ${paths.get(edge.target)}`, animated: false, style: { stroke: colors[edge.kind], strokeWidth: 1.6 }, markerEnd: { type: MarkerType.ArrowClosed, color: colors[edge.kind] } })),
  }
}

export function GraphPreview({ view, comparison, side }: { view: View; comparison?: View; side?: 'before' | 'after' }) {
  const graph = useMemo(() => layout(view), [view])
  const key = (node: View['nodes'][number]) => `${node.path}:${node.kind}:${node.symbol ?? ''}`
  const other = new Set(comparison?.nodes.map(key) ?? [])
  const changedIds = new Set(comparison ? view.nodes.filter(node => !other.has(key(node))).map(node => node.id) : [])
  return <section><p>{view.nodes.length}/{view.total_nodes} node · {view.edges.length}/{view.total_edges} cạnh trong phạm vi xem{view.truncated ? ' · đã giới hạn' : ''}</p>
    {comparison && <p>{side === 'before' ? 'Viền cam: thành phần bỏ so với B/target.' : 'Viền xanh: thành phần thêm so với A/base.'} So sánh trên phạm vi node đang hiển thị; tổng delta ở bảng chi tiết.</p>}
    <div className="graph-frame"><ReactFlow key={`${view.commit}-${view.nodes[0]?.id ?? ''}`} nodes={graph.nodes.map(node => changedIds.has(node.id) ? { ...node, className: 'graph-change-highlight', style: { ...node.style, border: `2px solid ${side === 'before' ? 'var(--warning)' : 'var(--positive)'}`, background: side === 'before' ? 'var(--change-removed-bg)' : 'var(--change-added-bg)' } } : node)} edges={graph.edges} fitView nodesDraggable={false} minZoom={0.15} maxZoom={2}><Background /><Controls /></ReactFlow></div></section>
}

function ExplorerWorkspace({ embedded = false }: { embedded?: boolean }) {
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
  const [commits, setCommits] = useState<components['schemas']['RepositoryOverview'] | null>(null)
  const [commitError, setCommitError] = useState('')
  const [resumeStatus, setResumeStatus] = useState<'loading' | 'empty' | 'restored' | 'unavailable'>('loading')
  const [loadedScope, setLoadedScope] = useState('')
  const [impactFailure, setImpactFailure] = useState<{ scope: string; message: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [refresh, setRefresh] = useState(0)
  const [tab, setTab] = useState('graph')
  const [list, setList] = useState<GraphNode[]>([])
  const [offset, setOffset] = useState(0)
  const [focusOnly, setFocusOnly] = useState(true)
  const [showSymbols, setShowSymbols] = useState(false)
  const [showStructure, setShowStructure] = useState(false)
  const [showEdgeLabels, setShowEdgeLabels] = useState(false)
  const [treeCollapsed, setTreeCollapsed] = useState(false)
  const [detailsCollapsed, setDetailsCollapsed] = useState(false)
  const [graphExpanded, setGraphExpanded] = useState(false)
  const [showSource, setShowSource] = useState(false)
  const [expanded, setExpanded] = useState<string[]>([])
  const requestId = useRef(0)
  const navigationId = useRef(0)
  const interactionId = useRef(0)
  const flight = useRef(false)
  const bootstrapped = useRef(false)
  const mounted = useRef(false)
  const heading = useRef<HTMLHeadingElement>(null)
  const flow = useRef<ReactFlowInstance | null>(null)
  const base = `/projects/${projectId}/snapshots/${commit}`
  const usable = /^[0-9a-f]{40}$/.test(commit)
  const selectedEntry = tree?.entries.find(entry => entry.path === path)
  const graphFocus = focusOnly && selectedEntry?.kind === 'file' ? path : ''
  const dataScope = `${base}:${graphFocus}:${offset}:${refresh}`
  const loading = usable && loadedScope !== dataScope
  const impactError = impactFailure?.scope === `${base}:${path}` ? impactFailure.message : ''
  const currentEvidence = evidence?.commit === commit && evidence.path === path ? evidence : null
  useEffect(() => {
    let cancelled = false
    productRequest<components['schemas']['RepositoryOverview']>(`/projects/${projectId}/repository`)
      .then(value => { if (!cancelled) { setCommits(value); setInput(previous => previous || value.commits[0]?.sha || '') } })
      .catch(cause => { if (!cancelled) setCommitError(cause instanceof Error ? cause.message : 'Chưa đọc được danh sách commit.') })
    return () => { cancelled = true }
  }, [projectId])
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
    setEvidence(proof ?? null); setShowSource(false); setSource(null); setCalls(null)
    setSearchParams(previous => { const next = new URLSearchParams(previous); next.set('path', selected); return next })
    setTab('details')
    setDetailsCollapsed(false)
  }, [setSearchParams])

  useEffect(() => {
    if (!usable) return
    let cancelled = false
    const id = ++requestId.current
    const active = () => !cancelled && id === requestId.current
    Promise.allSettled([
      productRequest<View>(`${base}/graph${graphFocus ? '?focus=' + encodeURIComponent(graphFocus) : ''}`),
      productRequest<Tree>(`${base}/tree`), productRequest<Hotspots>(`${base}/hotspots`),
      productRequest<GraphNode[]>(`${base}/nodes?offset=${offset}`),
    ]).then(([graph, entries, hubs, nodes]) => {
      if (!active()) return
      setView(graph.status === 'fulfilled' ? graph.value : null)
      setTree(entries.status === 'fulfilled' ? entries.value : null)
      setHotspots(hubs.status === 'fulfilled' ? hubs.value : null)
      setList(nodes.status === 'fulfilled' ? nodes.value : [])
      const failed = [graph, entries, hubs, nodes].filter(result => result.status === 'rejected')
      if (failed.length) setError(failed.length === 4 ? 'Chưa đọc được snapshot đã lưu. Hãy tải snapshot để thử lại.' : 'Một phần dữ liệu chưa tải được. Các phần còn lại vẫn có thể sử dụng; bấm Thử lại để kết nối lại.')
      else setError('')
    }).finally(() => { if (active()) setLoadedScope(dataScope) })
    return () => { cancelled = true }
  }, [base, usable, dataScope, graphFocus, offset])

  useEffect(() => {
    if (!usable || !path) return
    let cancelled = false
    productRequest<Impact>(`${base}/impact?path=${encodeURIComponent(path)}`)
      .then(value => { if (!cancelled) { setImpact({ scope: `${base}:${path}`, data: value }); setImpactFailure(null) } })
      .catch(cause => { if (!cancelled) { setImpact(null); setImpactFailure({ scope: `${base}:${path}`, message: cause instanceof Error ? cause.message : 'Chưa đọc được ảnh hưởng của file.' }) } })
    return () => { cancelled = true }
  }, [base, path, usable, refresh])

  const openSnapshot = useCallback(async (requestedCommit: string) => {
    if (flight.current) return
    flight.current = true; setBusy(true); setError(''); setView(null); setTree(null); setImpact(null); setSource(null); setCalls(null); setEvidence(null); setOffset(0)
    interactionId.current += 1
    const generation = navigationId.current
    const active = () => mounted.current && generation === navigationId.current
    try {
      const result = await productRequest<Info>(`/projects/${projectId}/snapshots`, 'POST', { commit: requestedCommit })
      if (active()) { setInfo(result); setSearchParams(previous => { const next = new URLSearchParams(previous); next.set('commit', requestedCommit); next.delete('path'); return next }); setRefresh(value => value + 1); setTab('tree') }
    } catch (cause) { if (active()) setError(cause instanceof Error ? cause.message : 'Không phân tích được snapshot.') }
    finally { flight.current = false; if (mounted.current) setBusy(false) }
  }, [projectId, setSearchParams])

  useEffect(() => {
    // Restore first; reopening a saved URL never reacquires from GitHub silently.
    if (resumeStatus !== 'empty' || searchParams.has('commit') || !commits?.commits.length || bootstrapped.current) return
    bootstrapped.current = true
    void openSnapshot(commits.commits[0]!.sha)
  }, [resumeStatus, searchParams, commits, openSnapshot])

  async function materialize(event: React.FormEvent) {
    event.preventDefault()
    await openSnapshot(input)
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
  const displayedView = useMemo(() => {
    if (!currentView) return null
    const nodes = currentView.nodes.filter(node => node.kind === 'file' || (node.kind === 'directory' ? showStructure : showSymbols))
    const visible = new Set(nodes.map(node => node.id))
    return { ...currentView, nodes, edges: currentView.edges.filter(edge => visible.has(edge.source) && visible.has(edge.target)) }
  }, [currentView, showSymbols, showStructure])
  const graph = useMemo(() => layout(displayedView, showEdgeLabels), [displayedView, showEdgeLabels])
  const selectedNodeIds = new Set(displayedView?.nodes.filter(node => node.path === path).map(node => node.id) ?? [])
  const selectedFileNodes = graph.nodes.filter(node => selectedNodeIds.has(node.id) && node.data.kind === 'file')
  function expandGraph() {
    setGraphExpanded(value => !value)
    if (!graphExpanded) requestAnimationFrame(() => document.getElementById('explorer-graph-pane')?.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }))
  }
  function focusSelected() {
    void flow.current?.fitView({ nodes: selectedFileNodes, padding: .5, minZoom: .9, maxZoom: 1.1, duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 180 })
  }
  const selectedImpact = impact?.scope === `${base}:${path}` ? impact.data : null
  const calls = callResult?.scope === `${base}:${path}` ? callResult.data : null
  const currentTree = tree?.commit === commit ? tree : null
  const callNodes = new Map([...(currentView?.nodes ?? []), ...(calls?.nodes ?? [])].map(node => [node.id, node]))
  return <section className={`explorer-page${embedded ? ' is-embedded' : ''}`} aria-label="Không gian khám phá repository">{!embedded && <><Link className="back-link" to={`/app/projects/${projectId}`}>← Về dự án</Link><p className="eyebrow">CẤU TRÚC VÀ QUAN HỆ PHỤ THUỘC</p><h1 ref={heading} tabIndex={-1}>Khám phá repository</h1></>}
    <form className="explorer-toolbar" onSubmit={materialize} aria-busy={busy}><div className="commit-field"><label htmlFor="snapshot-sha">Phiên bản mã nguồn</label><input id="snapshot-sha" list="explorer-commits" value={input} onChange={e => setInput(e.target.value)} pattern="[0-9a-f]{40}" required minLength={40} maxLength={40} disabled={busy} placeholder="Chọn commit hoặc dán SHA đầy đủ" /><datalist id="explorer-commits">{commits?.commits.map(item => <option key={item.sha} value={item.sha}>{item.message}</option>)}</datalist></div><button className="primary-button" disabled={busy || !/^[0-9a-f]{40}$/.test(input)}>{busy ? 'Đang chuẩn bị snapshot…' : 'Mở phiên bản'}</button>{usable && <button type="button" disabled={loading || busy} onClick={() => setRefresh(value => value + 1)}>Thử lại</button>}</form>
    <p className="field-hint">{commits ? `${commits.full_name} · ${commits.default_branch}` : 'Đọc repository GitHub public'} · Python / JavaScript · Phân tích tĩnh, không chạy mã nguồn hoặc gọi AI.</p>
    {commitError && <FormNotice error>{commitError} Bạn vẫn có thể dán SHA đầy đủ để mở snapshot.</FormNotice>}
    {error && <FormNotice error>{error}</FormNotice>}{busy || loading ? <div className="explorer-loading" role="status"><span className="loading-indicator" />{busy ? 'Đang chuẩn bị cây thư mục và quan hệ phụ thuộc…' : 'Đang đọc dữ liệu snapshot…'}</div> : !currentTree && !currentView && <FormNotice>Chọn phiên bản mã nguồn để xem cây thư mục. Liên kết có commit đã lưu chỉ đọc cache; bấm Mở phiên bản nếu cần tải lại.</FormNotice>}
    <ResumeState projectId={projectId ?? ''} value={{ commit, path: path || null, tab: tab === 'tree' ? 'tree' : tab === 'details' ? 'details' : 'graph', focus_only: focusOnly, expanded_paths: expanded }} ready={!!currentView || !!currentTree} restore={restore} onLoaded={saved => setResumeStatus(saved === undefined ? 'unavailable' : saved ? 'restored' : 'empty')} />
    {(currentView || currentTree) && <><div className="graph-summary"><span>Snapshot <code>{commit.slice(0, 8)}</code></span>{currentView && <><span>{currentView.coverage.analyzed_files.length} file đã phân tích</span><span>{currentView.coverage.status === 'complete' ? 'Trong phạm vi hỗ trợ' : 'Phạm vi phân tích chưa đầy đủ'}</span>{currentView.truncated && <strong>Graph đã giới hạn 150 node; dùng danh sách hoặc focus để xem tiếp.</strong>}</>}</div>
      {info?.commit === commit && info.excluded_count > 0 && <p>{info.excluded_count} đường dẫn không được đọc/lưu source theo chính sách.</p>}
      {currentView && <CoverageDetails coverage={currentView.coverage} />}
      <div className="explorer-layout-controls" role="group" aria-label="Bố trí không gian mã nguồn"><span>Không gian làm việc</span><button type="button" aria-controls="explorer-tree-pane" aria-pressed={!treeCollapsed && !graphExpanded} onClick={() => { if (graphExpanded) { setGraphExpanded(false); setTreeCollapsed(false) } else setTreeCollapsed(value => !value) }}>Cây thư mục</button><button type="button" aria-controls="explorer-detail-pane" aria-pressed={!detailsCollapsed && !graphExpanded} onClick={() => { if (graphExpanded) { setGraphExpanded(false); setDetailsCollapsed(false) } else setDetailsCollapsed(value => !value) }}>Chi tiết file</button><button className="graph-expand-button" type="button" aria-controls="explorer-graph-pane" aria-pressed={graphExpanded} onClick={expandGraph}>{graphExpanded ? 'Khôi phục bố cục' : 'Mở rộng graph'}</button></div>
      <div className="explorer-tabs" role="group" aria-label="Vùng khám phá">{[['tree', 'Cây thư mục'], ['graph', 'Graph'], ['details', 'Chi tiết']].map(([value, label]) => <button type="button" key={value} aria-pressed={tab === value} onClick={() => setTab(value ?? 'graph')}>{label}</button>)}</div>
      {graphExpanded && path && <p className="graph-selection-note" role="status">Đã chọn <code>{path}</code>. Mở Chi tiết file để xem ảnh hưởng và mã nguồn.</p>}
      <div className={`explorer-grid tab-${tab}${treeCollapsed ? ' tree-collapsed' : ''}${detailsCollapsed ? ' details-collapsed' : ''}${graphExpanded ? ' graph-expanded' : ''}`}><aside id="explorer-tree-pane" className="explorer-tree">{currentTree ? <RepositoryTreeView tree={treeValue(currentTree, currentTree.repository_url, commit)} selectedPath={path} onSelect={selected => choose(selected)} expandedPaths={expanded} onExpand={(folder, open) => setExpanded(previous => open === previous.includes(folder) ? previous : open ? [...previous, folder].slice(0, 1000) : previous.filter(item => item !== folder))} /> : <FormNotice>Cây thư mục chưa tải được. Bấm Thử lại để đọc lại; graph vẫn sử dụng được.</FormNotice>}</aside>
        <section id="explorer-graph-pane" className="explorer-canvas"><h2>Quan hệ phụ thuộc</h2><p className="graph-legend">File sử dụng → file được sử dụng · Phân tích tĩnh</p>
          <div className="graph-options"><label className="checkbox-label"><input type="checkbox" checked={focusOnly} onChange={e => setFocusOnly(e.target.checked)} />Focus vào file đã chọn</label><label className="checkbox-label"><input type="checkbox" checked={showSymbols} onChange={e => setShowSymbols(e.target.checked)} />Hiện hàm và lớp</label><label className="checkbox-label"><input type="checkbox" checked={showStructure} onChange={e => setShowStructure(e.target.checked)} />Hiện thư mục</label><label className="checkbox-label"><input type="checkbox" checked={showEdgeLabels} onChange={e => setShowEdgeLabels(e.target.checked)} />Nhãn quan hệ</label></div>
          {displayedView && <p className="graph-legend">{displayedView.nodes.length} node đang hiển thị · {showSymbols ? 'Bao gồm symbol' : showStructure ? 'Cấp file và thư mục' : 'Cấp file'}</p>}
          <div className="graph-edge-legend"><span className="legend-imports">Import</span><span className="legend-calls">Lời gọi tĩnh</span>{showStructure && <span className="legend-contains">Cấu trúc</span>}</div>
          <button className="graph-focus-button" type="button" disabled={!selectedFileNodes.length} onClick={focusSelected}>Đến file đã chọn</button>
          {currentView ? <div className="graph-frame"><ReactFlow<Node, Edge>
            key={`${commit}-${focusOnly}-${focusOnly ? path : ''}-${graphExpanded}-${treeCollapsed}-${detailsCollapsed}-${showSymbols}-${showStructure}`}
            onInit={instance => { flow.current = instance }}
            nodes={graph.nodes.map(node => ({ ...node, selected: selectedNodeIds.has(node.id), style: { ...node.style, ...(selectedNodeIds.has(node.id) ? { borderColor: 'var(--primary)', boxShadow: '0 0 0 2px var(--selected-surface)' } : {}) } }))}
            edges={graph.edges.map(edge => ({ ...edge, style: { ...edge.style, opacity: selectedNodeIds.size && !selectedNodeIds.has(edge.source) && !selectedNodeIds.has(edge.target) ? .24 : 1 } }))}
            fitView fitViewOptions={{ padding: .18, maxZoom: 1.1, ...(focusOnly && selectedFileNodes.length ? { nodes: selectedFileNodes, minZoom: .75 } : {}) }} minZoom={0.15} maxZoom={2.5} nodesDraggable={false}
            onNodeClick={(_, node) => { const value = currentView.nodes.find(item => item.id === node.id); if (value) choose(value.path, value.evidence) }}
            onEdgeClick={(_, edge) => { const value = currentView.edges.find(item => item.id === edge.id); if (value) choose(value.evidence.path, value.evidence) }}
          ><Background /><Controls /></ReactFlow></div> : <FormNotice>Graph chưa tải được. Cây thư mục và thông tin file vẫn sử dụng được.</FormNotice>}
          {displayedView && !displayedView.nodes.length && <FormNotice>Chưa có node phù hợp với chế độ xem này. Thử bật Hiện thư mục hoặc Hiện hàm và lớp để xem phần dữ liệu còn lại.</FormNotice>}
          <details><summary>Danh sách thay thế — dùng bàn phím</summary><ul className="graph-node-list">{list.map(node => <li key={node.id}><button type="button" onClick={() => choose(node.path, node.evidence)}>{node.path}{node.symbol ? ` · ${node.symbol}` : ''}</button>{node.kind !== 'directory' && <button type="button" onClick={() => void readCalls(node)}>Call paths</button>}</li>)}</ul><div className="dialog-actions"><button disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 100))}>Trước</button><button disabled={list.length < 100} onClick={() => setOffset(value => value + 100)}>Tiếp</button></div></details>
          <details><summary>Hotspots cấu trúc</summary>{hotspots ? <>{hotspots.cycles.length ? hotspots.cycles.map((cycle, index) => <p key={index}>Vòng phụ thuộc: {cycle.map(file => <button key={file} onClick={() => choose(file)}>{file}</button>)}</p>) : <p>Không quan sát thấy vòng trong graph đã phân tích.</p>}<ul>{Object.entries(hotspots.fan_in).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([file, count]) => <li key={file}><button onClick={() => choose(file)}>{file}</button> · fan-in {count} · fan-out {hotspots.fan_out[file]}</li>)}</ul><p>Chỉ số cấu trúc, chưa phải lỗi hoặc điểm rủi ro.</p></> : <FormNotice>Hotspots chưa tải được; chưa có kết luận về vòng phụ thuộc.</FormNotice>}</details>
        </section><aside id="explorer-detail-pane" className="explorer-inspector"><h2>Chi tiết và ảnh hưởng</h2>{path ? <><code className="selected-path">{path}</code><p>Commit: {commit.slice(0, 12)}</p>{currentEvidence && <p>{currentEvidence.kind === "metadata" ? "Bằng chứng metadata của file/thư mục" : `Bằng chứng dòng ${currentEvidence.line_start}–${currentEvidence.line_end}`}</p>}<button disabled={selectedEntry?.kind === 'directory'} onClick={() => void readSource()}>Xem đoạn mã nguồn</button>
          {showSource && source?.path === path && source.commit === commit && <pre className="source-range" tabIndex={0} aria-label="Đoạn mã nguồn"><code>{source.content}</code></pre>}
          {impactError && <FormNotice error>{impactError}</FormNotice>}
          {!selectedImpact && !impactError && <p role="status">Đang đọc ảnh hưởng tĩnh của file…</p>}
          {selectedImpact && <div className="impact-metrics"><ImpactOverview key={`${base}:${path}`} value={selectedImpact} onChoose={choose} assumedChange /><h4>Trực tiếp</h4>{selectedImpact.direct.map(file => <button key={file} onClick={() => choose(file)}>{file}</button>)}<h4>Gián tiếp</h4>{selectedImpact.indirect.map(file => <button key={file} onClick={() => choose(file)}>{file}</button>)}</div>}
          {calls && <div><h3>Static call paths — chưa phải runtime trace</h3>{calls.paths.map((items, index) => <p key={index}>{items.map((id, step) => { const node = callNodes.get(id); return <span key={`${id}-${step}`}>{step > 0 && ' → '}<button type="button" disabled={!node} onClick={() => node && choose(node.path, node.evidence)}>{node?.symbol ?? node?.path ?? id.slice(0, 10)}</button></span> })}</p>)}{calls.truncated && <p>Đã dừng ở giới hạn duyệt.</p>}<p>{calls.unresolved.length} điểm chưa giải được trong các file liên quan.</p><ul>{calls.unresolved.slice(0, 50).map((item, index) => <li key={index}><button type="button" onClick={() => choose(item.path)}>{item.path}:{item.line}</button> · {item.reason}{item.reference ? ` · ${item.reference}` : ''}</li>)}</ul>{calls.unresolved.length > 50 && <p>Đang liệt kê 50 điểm đầu; số tổng phía trên vẫn giữ nguyên.</p>}</div>}
          <p><Link className="text-link" to={`/app/projects/${projectId}/what-if?commit=${commit}&path=${encodeURIComponent(path)}`}>Thử thay đổi file này →</Link></p>
          <Notes key={commit} projectId={projectId ?? ''} commit={commit} path={path} />
        </> : <p>Chọn file, symbol hoặc cạnh để đối chiếu bằng chứng.</p>}</aside>
      </div><Assistance key={base} base={base} path={path} choose={choose} /></>}
  </section>
}

export function Explorer({ embedded = false }: { embedded?: boolean }) {
  const { projectId } = useParams()
  return <ExplorerWorkspace key={projectId} embedded={embedded} />
}
