export function RepositoryArtwork() {
  return <figure className="repository-artwork">
    <div className="auth-art-window" aria-hidden="true">
      <div className="auth-art-toolbar"><span className="auth-art-dots"><i /><i /><i /></span><span>workspace / dependency map</span><span>⌘</span></div>
      <svg viewBox="0 0 560 310" fill="none" className="auth-art-map">
        <defs><pattern id="auth-map-grid" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="var(--border-strong)" /></pattern></defs>
        <rect width="560" height="310" fill="url(#auth-map-grid)" />
        <g stroke="var(--graph-imports)" strokeWidth="1.7"><path d="M174 154H216Q232 154 232 138V84Q232 68 250 68H300" /><path d="M174 154H300" /><path d="M174 154H216Q232 154 232 170V224Q232 240 250 240H300" /></g>
        <g fill="var(--graph-imports)"><path d="m294 64 6 4-6 4M294 150l6 4-6 4M294 236l6 4-6 4" /></g>
        <g className="auth-art-node auth-art-origin"><rect x="34" y="120" width="140" height="68" rx="10" /><rect x="34" y="120" width="4" height="68" rx="2" className="auth-art-accent" /><text x="52" y="146" className="auth-art-node-label">parser.py</text><text x="52" y="168" className="auth-art-node-meta">file thay đổi</text></g>
        <g className="auth-art-node auth-art-dependent"><rect x="300" y="38" width="202" height="60" rx="10" /><text x="318" y="64" className="auth-art-node-label">analyzer.py</text><text x="318" y="83" className="auth-art-node-meta">quan hệ phụ thuộc</text></g>
        <g className="auth-art-node auth-art-dependent"><rect x="300" y="124" width="202" height="60" rx="10" /><text x="318" y="150" className="auth-art-node-label">test_parser.py</text><text x="318" y="169" className="auth-art-node-meta">kiểm thử hiện có</text></g>
        <g className="auth-art-node auth-art-dependent"><rect x="300" y="210" width="202" height="60" rx="10" /><text x="318" y="236" className="auth-art-node-label">report.py</text><text x="318" y="255" className="auth-art-node-meta">lần theo bằng chứng</text></g>
        <g fill="var(--primary)"><circle cx="174" cy="154" r="4" /><circle cx="300" cy="68" r="3" /><circle cx="300" cy="154" r="3" /><circle cx="300" cy="240" r="3" /></g>
      </svg>
      <div className="auth-art-code"><span>diff / parser.py</span><code><b>+</b> return resolve_dependencies(source)</code></div>
    </div>
    <figcaption><span className="auth-art-caption-line" />Từ một thay đổi, nhìn thấy các kết nối.<small>Sơ đồ minh hoạ</small></figcaption>
  </figure>
}
