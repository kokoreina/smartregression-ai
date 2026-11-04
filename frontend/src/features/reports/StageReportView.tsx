import type { components } from '../../types/generated'
import { EvidenceItem } from '../../components/EvidenceItem'
import { statusClass, statusLabel, type StageAnalysisReport } from './stageReport'

type StageStatus = components['schemas']['StageAnalysisReport']['analysis_status']
type StageResult = { status: StageStatus; limitations?: components['schemas']['StageIssue'][]; reason?: string | null; error_code?: string | null }

const TIER_LABEL: Record<1 | 2 | 3, string> = {
  1: 'Thay đổi trực tiếp',
  2: 'Phụ thuộc trực tiếp',
  3: 'Phụ thuộc gián tiếp',
}

function StageChip({ name, result }: { name: string; result: StageResult }) {
  const cls = statusClass(result.status)
  return (
    <span className={`stage-chip ${cls}`} title={result.error_code ?? result.reason ?? undefined}>
      {name}
    </span>
  )
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return <div className="section-heading"><h2>{children}</h2></div>
}

/** Hiển thị nhãn data_kind phân biệt DEMO / REAL */
function DataKindBadge({ kind }: { kind: 'demo' | 'real' }) {
  return kind === 'real'
    ? <span className="badge badge-real">REAL</span>
    : <span className="badge">DEMO</span>
}

/** Hiển thị commit SHA rút gọn với tooltip full */
function CommitCode({ commit }: { commit: string }) {
  return <code title={commit}>{commit.slice(0, 10)}…</code>
}

/** Vùng thông tin định danh chạy phân tích */
function IdentitySection({ report }: { report: StageAnalysisReport }) {
  const { identity, analysis_status, data_kind, report_id, analysis_duration_seconds } = report
  return (
    <section className="card" aria-label="Thông tin chạy phân tích">
      <div className="section-heading">
        <h2>Repository &amp; Commits</h2>
        <DataKindBadge kind={data_kind} />
      </div>
      <div className="commits">
        <div>
          <span className="label">Repository</span>
          <code>{identity.repository_id}</code>
        </div>
        <div>
          <span className="label">Base commit</span>
          <CommitCode commit={identity.base.commit} />
        </div>
        <span aria-hidden="true">→</span>
        <div>
          <span className="label">Target commit</span>
          <CommitCode commit={identity.target.commit} />
        </div>
      </div>
      <p className="muted">
        Run ID: <code>{report_id}</code> ·
        Trạng thái phân tích:{' '}
        <strong className={statusClass(analysis_status)}>{statusLabel(analysis_status)}</strong>
        {analysis_duration_seconds != null && ` · ${analysis_duration_seconds}s`}
      </p>
    </section>
  )
}

/** Thanh trạng thái các stage */
function StageStatusBar({ report }: { report: StageAnalysisReport }) {
  const s = report.stages
  const stageMap: [string, StageResult][] = [
    ['Snapshots', s.snapshots],
    ['Changes', s.changes],
    ['Graph', s.graph],
    ['Impact', s.impact],
    ['Inventory', s.inventory],
    ['Retrieval', s.retrieval],
    ['Evidence', s.evidence],
    ['Review', s.review_ordering],
  ]
  return (
    <section className="card stage-status-bar" aria-label="Trạng thái các bước phân tích">
      <SectionHeader>Trạng thái pipeline</SectionHeader>
      <div className="stage-chips" role="list" aria-label="Danh sách bước phân tích">
        {stageMap.map(([name, result]) => (
          <div key={name} role="listitem">
            <StageChip name={name} result={result} />
          </div>
        ))}
      </div>
    </section>
  )
}

/** Hiển thị review ordering candidates (Tier 1/2/3) */
function ReviewOrderSection({ report }: { report: StageAnalysisReport }) {
  const stage = report.stages.review_ordering
  if (stage.status === 'not_implemented' || stage.status === 'not_run') {
    return (
      <section className="card" aria-label="Thứ tự xem xét">
        <SectionHeader>Thứ tự xem xét</SectionHeader>
        <p className="muted">Chưa có dữ liệu ({statusLabel(stage.status)}).</p>
      </section>
    )
  }
  if (stage.status === 'failed') {
    return (
      <section className="card" aria-label="Thứ tự xem xét">
        <SectionHeader>Thứ tự xem xét</SectionHeader>
        <p className="muted status-failed">Bước xem xét thất bại: <code>{stage.error_code}</code></p>
      </section>
    )
  }
  const data = stage.data
  if (!data) return null
  const tiers = ([1, 2, 3] as const).map((t) => ({
    tier: t,
    items: data.candidates.filter((c) => c.tier === t),
  }))

  return (
    <section className="card" aria-label="Thứ tự xem xét">
      <div className="section-heading">
        <h2>Thứ tự xem xét <span className="count">{data.candidates.length}</span></h2>
        <span className="muted" style={{ fontSize: 11 }}>rule {data.rule_version}</span>
      </div>
      {stage.limitations && stage.limitations.length > 0 && (
        <div className="evidence-issue" role="note">
          <span className="evidence-issue-label">Giới hạn:</span>{' '}
          {stage.limitations.map((l) => <code key={l.code}>{l.code}{l.path ? `:${l.path}` : ''}</code>)}
        </div>
      )}
      {tiers.map(({ tier, items }) =>
        items.length === 0 ? null : (
          <div key={tier}>
            <h3 className="tier-heading">
              Tier {tier} — {TIER_LABEL[tier]} <span className="count">{items.length}</span>
            </h3>
            {items.map((c) => (
              <article key={`${c.path}/${c.symbol ?? ''}`} className="review-item">
                <code>{c.path}</code>
                {c.symbol && <> · <strong>{c.symbol}</strong></>}
                <span className="muted"> — {c.reason}</span>
              </article>
            ))}
          </div>
        ),
      )}
    </section>
  )
}

/** Hiển thị evidence items từ stage v2 */
function EvidenceSection({ report }: { report: StageAnalysisReport }) {
  const stage = report.stages.evidence
  if (stage.status === 'not_implemented' || stage.status === 'not_run') {
    return (
      <section className="card" aria-label="Bằng chứng">
        <SectionHeader>Bằng chứng</SectionHeader>
        <p className="muted">Chưa có bằng chứng ({statusLabel(stage.status)}).</p>
      </section>
    )
  }
  if (stage.status === 'failed') {
    return (
      <section className="card" aria-label="Bằng chứng">
        <SectionHeader>Bằng chứng</SectionHeader>
        <p className="muted status-failed">Bước bằng chứng thất bại: <code>{stage.error_code}</code></p>
      </section>
    )
  }
  const items = stage.data?.items ?? []
  return (
    <section className="card" aria-label="Bằng chứng">
      <div className="section-heading">
        <h2>Bằng chứng <span className="count">{items.length}</span></h2>
        {stage.status === 'partial' && (
          <span className="stage-chip status-partial">Một phần</span>
        )}
      </div>
      {items.length === 0
        ? <p className="muted">Không có bằng chứng trong báo cáo này.</p>
        : items.map((item) => <EvidenceItem key={item.id} evidence={item} />)
      }
    </section>
  )
}

/** Hiển thị impact candidates */
function ImpactSection({ report }: { report: StageAnalysisReport }) {
  const stage = report.stages.impact
  if (stage.status === 'not_implemented' || stage.status === 'not_run') {
    return (
      <section className="card" aria-label="Phân tích ảnh hưởng">
        <SectionHeader>Phân tích ảnh hưởng</SectionHeader>
        <p className="muted">Chưa có dữ liệu ({statusLabel(stage.status)}).</p>
      </section>
    )
  }
  if (stage.status === 'failed') {
    return (
      <section className="card" aria-label="Phân tích ảnh hưởng">
        <SectionHeader>Phân tích ảnh hưởng</SectionHeader>
        <p className="muted status-failed">Thất bại: <code>{stage.error_code}</code></p>
      </section>
    )
  }
  const candidates = stage.data?.candidates ?? []
  return (
    <section className="card" aria-label="Phân tích ảnh hưởng">
      <div className="section-heading">
        <h2>Ảnh hưởng <span className="count">{candidates.length}</span></h2>
      </div>
      {candidates.length === 0
        ? <p className="muted">Không có thành phần bị ảnh hưởng.</p>
        : candidates.map((c) => (
          <article key={c.id} className="review-item">
            <code>{c.path}</code>
            {c.symbol && <> · <strong>{c.symbol}</strong></>}
            <span className="muted"> — {c.relationship}</span>
            {c.explanation && <p style={{ margin: '4px 0 0', fontSize: 13 }}>{c.explanation}</p>}
          </article>
        ))
      }
    </section>
  )
}

/** Root view cho StageAnalysisReport (v2) — Task 2.18 */
export function StageReportView({ report }: { report: StageAnalysisReport }) {
  return (
    <>
      <IdentitySection report={report} />
      <StageStatusBar report={report} />
      <div className="columns">
        <div>
          <ReviewOrderSection report={report} />
          <ImpactSection report={report} />
        </div>
        <div>
          <EvidenceSection report={report} />
        </div>
      </div>
    </>
  )
}

