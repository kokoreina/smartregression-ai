import type { AnalysisReport } from './demo'

export function ReportView({ report }: { report: AnalysisReport }) {
  return <>
    <section className="card">
      <div className="section-heading"><h2>Repository & commits</h2><span className="badge">DEMO</span></div>
      <p>{report.repository}</p>
      <div className="commits">
        <div><span className="label">Base commit</span><code>{report.commits.base}</code></div>
        <span aria-hidden="true">→</span>
        <div><span className="label">Target commit</span><code>{report.commits.target}</code></div>
      </div>
      <p className="muted">Phân tích: {report.analysis_status} · Thực thi: {report.execution_status}</p>
    </section>
    <div className="columns">
      <section className="card">
        <h2>Ảnh hưởng minh họa <span className="count">{report.findings.length}</span></h2>
        {report.findings.length === 0 && <p>Chưa có nhận định ảnh hưởng.</p>}
        {report.findings.map((finding) => <article key={finding.id}>
          <code>{finding.component.path} · {finding.component.symbol ?? 'file'}</code>
          <p>{finding.explanation}</p>
          <div className="links">{finding.evidence_ids.map((id) => <a key={id} href={`#${id}`}>{id}</a>)}</div>
        </article>)}
        <h3>Bằng chứng</h3>
        {report.evidence.length === 0 && <p>Chưa có bằng chứng.</p>}
        {report.evidence.map((item) => <article id={item.id} key={item.id} className="evidence">
          <strong>{item.id}</strong>
          <p><code>{item.path}:{item.line_start}–{item.line_end}</code></p>
          <p className="muted">Symbol: {item.symbol ?? '—'} · Commit: <code>{item.commit}</code></p>
          {item.excerpt && <pre>{item.excerpt}</pre>}
        </article>)}
      </section>
      <section className="card">
        <h2>Lựa chọn test <span className="count">{report.selection.selected.length}</span></h2>
        <p className="muted">Framework: {report.selection.framework}</p>
        <h3>Được chọn</h3>
        {report.selection.selected.length === 0 && <p>Không có test được chọn.</p>}
        {report.selection.selected.map((test) => <article key={test.test_id}>
          <code>{test.test_id}</code><p>{test.reason}</p>
          <div className="links">{test.evidence_ids?.map((id) => <a key={id} href={`#${id}`}>{id}</a>)}</div>
        </article>)}
        <h3>Bỏ qua</h3>
        {report.selection.skipped.length === 0 && <p>Không có test bị bỏ qua.</p>}
        {report.selection.skipped.map((test) => <article key={test.test_id}>
          <code>{test.test_id}</code><p>{test.reason}</p>
        </article>)}
        <p><strong>Fallback:</strong> {report.selection.fallback_reason ?? 'Không có trong minh họa'}</p>
        <p className="muted">Thời gian phân tích: {report.analysis_duration_seconds == null ? 'Chưa đo' : `${report.analysis_duration_seconds} s`}
          <br />Chi phí LLM: {report.llm_cost_usd == null ? 'Chưa đo' : `$${report.llm_cost_usd}`}</p>
      </section>
    </div>
  </>
}
