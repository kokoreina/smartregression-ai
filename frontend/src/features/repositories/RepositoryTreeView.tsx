import { useMemo, useState } from 'react'
import { buildTree, filterTree, treeText, type GitTree, type TreeNode } from './repositoryTree'

const kinds = { file: 'File', directory: 'Thư mục', symlink: 'Liên kết tượng trưng', submodule: 'Submodule' }

function Branch({ nodes, depth, searching, onSelect, selected, expandedPaths, onExpand }: {
  nodes: TreeNode[]; depth: number; searching: boolean; onSelect: (node: TreeNode) => void; selected?: string; expandedPaths?: string[]; onExpand?: (path: string, expanded: boolean) => void
}) {
  return <ul className="repo-tree-list">{nodes.map(node => <li key={node.path}>
    {node.kind === 'directory'
      ? <details key={`${node.path}-${searching}`} open={searching || (expandedPaths ? expandedPaths.includes(node.path) : depth < 1)} onToggle={event => { if (!searching) onExpand?.(node.path, event.currentTarget.open) }}>
          <summary aria-label={`Thư mục ${node.path}`}><span>{node.name}/</span></summary>
          <Branch nodes={node.children} depth={depth + 1} searching={searching} onSelect={onSelect} selected={selected} expandedPaths={expandedPaths} onExpand={onExpand} />
        </details>
      : <button type="button" className="tree-file" onClick={() => onSelect(node)} aria-pressed={selected === node.path}
          title={node.path}>{node.name}{node.kind !== 'file' && <small> [{node.kind}]</small>}</button>}
  </li>)}</ul>
}

export function RepositoryTreeView({ tree, onSelect, selectedPath, expandedPaths, onExpand }: { tree: GitTree; onSelect?: (path: string) => void; selectedPath?: string; expandedPaths?: string[]; onExpand?: (path: string, expanded: boolean) => void }) {
  const [query, setQuery] = useState('')
  const [selection, setSelected] = useState<TreeNode | null>(null)
  const selected = selectedPath === undefined ? selection : (() => {
    const entry = tree.entries.find(item => item.path === selectedPath)
    return entry ? { ...entry, name: entry.path.split('/').at(-1) ?? entry.path, children: [] } : null
  })()
  const nodes = useMemo(() => buildTree(tree.entries), [tree.entries])
  const visible = useMemo(() => filterTree(nodes, query), [nodes, query])
  const root = tree.repository_url.split('/').at(-1) ?? 'repository'
  const fileCount = tree.entries.filter(e => e.kind === 'file').length
  const folderCount = tree.entries.filter(e => e.kind === 'directory').length

  function download() {
    const text = `# ${tree.repository_url}\n# Commit: ${tree.commit}\n\n${treeText(nodes, root)}`
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `repository-tree-${tree.commit.slice(0, 10)}.txt`
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return <section className="repository-tree" aria-labelledby="tree-title">
    <div className="section-heading"><h3 id="tree-title">Cây thư mục dự án</h3>
      <button type="button" onClick={download}>Tải cây dạng văn bản</button></div>
    <p>{folderCount} thư mục · {fileCount} file · {tree.entries.length - folderCount - fileCount} liên kết/submodule</p>
    <p className="muted">Repo: <code>{tree.repository_url}</code><br />Dữ liệu Git tại target commit <code>{tree.commit}</code>. Chỉ liệt kê đường dẫn đã commit, không tải nội dung file và không gọi Gemini.</p>
    <label htmlFor="tree-search">Tìm file hoặc thư mục</label>
    <input id="tree-search" type="search" value={query} onChange={e => setQuery(e.target.value)}
      onKeyDown={e => { if (e.key === 'Enter') e.preventDefault() }} placeholder="Ví dụ: src, App.js, README" />
    <div className="tree-layout">
      <div className="tree-scroll" role="region" aria-label="Cấu trúc thư mục" tabIndex={0}>
        <strong className="tree-root">{root}/</strong>
        {visible.length ? <Branch nodes={visible} depth={0} searching={!!query.trim()} onSelect={node => { setSelected(node); onSelect?.(node.path) }} selected={selected?.path} expandedPaths={expandedPaths} onExpand={onExpand} />
          : <p role="status">{tree.entries.length ? 'Không tìm thấy đường dẫn phù hợp.' : 'Commit này có cây Git rỗng.'}</p>}
      </div>
      <div className="tree-selection" aria-live="polite">
        {selected ? <>
          <strong>{kinds[selected.kind]}</strong><p><code>{selected.path}</code></p>
          {selected.size != null && <p>Kích thước: {selected.size.toLocaleString('vi-VN')} byte</p>}
          {selected.kind !== 'file' && <p>Chỉ hiển thị liên kết; không truy cập đích hoặc repo con.</p>}
          <p className="muted">Cây thư mục cho biết vị trí file. Quan hệ phụ thuộc và ảnh hưởng cần kết quả phân tích mã nguồn.</p>
        </> : <p>Chọn một file để xem đường dẫn và kích thước. Mở hoặc thu gọn từng thư mục để khám phá dự án.</p>}
      </div>
    </div>
    <p className="muted">Các thư mục chỉ có trên máy như node_modules sẽ không xuất hiện nếu chưa được commit. Xem cây hỗ trợ nhiều loại file; phân tích ảnh hưởng hiện hỗ trợ Python.</p>
  </section>
}
