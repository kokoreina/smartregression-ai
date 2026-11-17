import type { components } from '../../types/generated'

export type GitTree = components['schemas']['RepositoryTree']
export type GitEntry = components['schemas']['RepositoryTreeEntry']
export type TreeNode = GitEntry & { name: string; children: TreeNode[] }

export function treeValue(value: unknown, url: string, commit: string): GitTree {
  if (!value || typeof value !== 'object' || !('schema_version' in value) || value.schema_version !== '1.0.0'
    || !('repository_url' in value) || value.repository_url !== url
    || !('commit' in value) || value.commit !== commit
    || !('tree_sha' in value) || typeof value.tree_sha !== 'string' || !/^[a-f0-9]{40}$/.test(value.tree_sha)
    || !('entries' in value) || !Array.isArray(value.entries) || value.entries.length > 5000) {
    throw new Error('Cây thư mục không khớp repository hoặc commit đã chọn.')
  }
  const paths = new Map<string, string>()
  for (const entry of value.entries) {
    if (!entry || typeof entry !== 'object' || typeof entry.path !== 'string'
      || entry.path.length > 2048 || entry.path.includes('\\')
      || Array.from(entry.path as string).some(char => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127)
      || entry.path.split('/').length > 40 || entry.path.split('/').some((p: string) => ['', '.', '..'].includes(p))
      || !['file', 'directory', 'symlink', 'submodule'].includes(entry.kind)
      || paths.has(entry.path)) throw new Error('Danh sách đường dẫn Git không hợp lệ.')
    if (['file', 'symlink'].includes(entry.kind)
      ? !Number.isSafeInteger(entry.size) || entry.size < 0
      : entry.size != null) throw new Error('Metadata kích thước file không hợp lệ.')
    paths.set(entry.path, entry.kind)
  }
  for (const path of paths.keys()) {
    const slash = path.lastIndexOf('/')
    if (slash !== -1 && paths.get(path.slice(0, slash)) !== 'directory') {
      throw new Error('Cây Git thiếu thư mục cha hoặc có đường dẫn mâu thuẫn.')
    }
  }
  return value as GitTree
}

export function buildTree(entries: GitEntry[]): TreeNode[] {
  const nodes = new Map(entries.map(e => [e.path, { ...e, name: e.path.split('/').at(-1)!, children: [] } as TreeNode]))
  const roots: TreeNode[] = []
  for (const node of nodes.values()) {
    const parent = nodes.get(node.path.slice(0, node.path.lastIndexOf('/')))
    if (node.path.includes('/') && parent) parent.children.push(node)
    else roots.push(node)
  }
  const sort = (list: TreeNode[]) => {
    list.sort((a, b) => Number(b.kind === 'directory') - Number(a.kind === 'directory')
      || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
    for (const node of list) sort(node.children)
  }
  sort(roots)
  return roots
}

export function filterTree(nodes: TreeNode[], query: string): TreeNode[] {
  const needle = query.trim().toLowerCase()
  if (!needle) return nodes
  return nodes.flatMap(node => {
    if (node.path.toLowerCase().includes(needle)) return [node]
    const children = filterTree(node.children, needle)
    return children.length ? [{ ...node, children }] : []
  })
}

export function treeText(nodes: TreeNode[], root: string): string {
  const lines = [root + '/']
  const walk = (items: TreeNode[], prefix: string) => {
    items.forEach((node, index) => {
      const last = index === items.length - 1
      const suffix = node.kind === 'directory' ? '/' : node.kind === 'file' ? '' : ` [${node.kind}]`
      lines.push(prefix + (last ? '└── ' : '├── ') + node.name + suffix)
      walk(node.children, prefix + (last ? '    ' : '│   '))
    })
  }
  walk(nodes, '')
  return lines.join('\n') + '\n'
}
