import type { components } from '../types/generated'

export type StageEvidence = components['schemas']['StageEvidence']
export type EvidenceReference = components['schemas']['EvidenceReference']

export type EvidenceItemData = StageEvidence | EvidenceReference

export interface EvidenceItemProps {
  evidence: EvidenceItemData
  className?: string
}

export type ResolutionStatus = 'resolved' | 'missing' | 'mismatched' | 'unverified'
export type SupportStatus = 'supported' | 'unsupported' | 'unverified'

const RESOLUTION_CONFIG: Record<
  ResolutionStatus,
  { label: string; indicator: string; badgeClass: string; description: string }
> = {
  resolved: {
    label: 'Đã xác minh nguồn',
    indicator: '✓',
    badgeClass: 'evidence-badge-resolved',
    description: 'Vị trí tệp và dòng khớp chính xác với snapshot.',
  },
  missing: {
    label: 'Thiếu nguồn',
    indicator: '✗',
    badgeClass: 'evidence-badge-missing',
    description: 'Tệp hoặc phạm vi dòng không tồn tại trong snapshot.',
  },
  mismatched: {
    label: 'Nội dung lệch',
    indicator: '!',
    badgeClass: 'evidence-badge-mismatched',
    description: 'Nội dung thực tế tại snapshot không khớp với đoạn trích dẫn.',
  },
  unverified: {
    label: 'Chưa kiểm chứng nguồn',
    indicator: '?',
    badgeClass: 'evidence-badge-unverified',
    description: 'Chưa đối chiếu với snapshot tin cậy của kho mã nguồn.',
  },
}

const SUPPORT_CONFIG: Record<
  SupportStatus,
  { label: string; indicator: string; badgeClass: string; description: string }
> = {
  supported: {
    label: 'Hỗ trợ kết luận',
    indicator: '✓',
    badgeClass: 'evidence-badge-supported',
    description: 'Bằng chứng chứng minh được nhận định ảnh hưởng.',
  },
  unsupported: {
    label: 'Không hỗ trợ kết luận',
    indicator: '✗',
    badgeClass: 'evidence-badge-unsupported',
    description: 'Bằng chứng không đủ cơ sở hỗ trợ nhận định ảnh hưởng.',
  },
  unverified: {
    label: 'Chưa kiểm chứng kết luận',
    indicator: '?',
    badgeClass: 'evidence-badge-unverified',
    description: 'Chưa có kết quả kiểm chứng hỗ trợ cho nhận định này.',
  },
}

function normalizeEvidence(evidence: EvidenceItemData) {
  const isStageEvidence = 'location' in evidence && evidence.location !== undefined

  const lineStart = isStageEvidence
    ? evidence.location.line_start
    : (evidence as EvidenceReference).line_start

  const lineEnd = isStageEvidence
    ? evidence.location.line_end
    : (evidence as EvidenceReference).line_end

  const commit =
    'snapshot' in evidence && evidence.snapshot
      ? evidence.snapshot.commit
      : (evidence as EvidenceReference).commit

  const snapshotId =
    'snapshot' in evidence && evidence.snapshot ? evidence.snapshot.snapshot_id : null

  const resolution: ResolutionStatus =
    'resolution' in evidence && evidence.resolution ? evidence.resolution : 'unverified'

  const support: SupportStatus =
    'support' in evidence && evidence.support ? evidence.support : 'unverified'

  const verificationReason =
    'verification_reason' in evidence ? evidence.verification_reason : null

  return {
    id: evidence.id,
    path: evidence.path,
    lineStart,
    lineEnd,
    commit,
    snapshotId,
    symbol: evidence.symbol ?? null,
    excerpt: evidence.excerpt ?? null,
    resolution,
    support,
    verificationReason,
  }
}

/**
 * Reusable component for rendering an individual evidence item (Task 2.06 / Task 2.18).
 *
 * Implements accessible status indicators (combines text, indicator icon, and color)
 * and distinguishes verified source/support states from unverified or mismatched states.
 */
export function EvidenceItem({ evidence, className = '' }: EvidenceItemProps) {
  const item = normalizeEvidence(evidence)
  const resMeta = RESOLUTION_CONFIG[item.resolution]
  const supMeta = SUPPORT_CONFIG[item.support]

  return (
    <article
      id={item.id}
      className={`evidence evidence-item ${className}`.trim()}
      aria-label={`Bằng chứng ${item.id}`}
    >
      <div className="evidence-header">
        <div className="evidence-identity">
          <strong className="evidence-id">{item.id}</strong>
          <span className="evidence-location">
            <code>
              {item.path}:{item.lineStart}–{item.lineEnd}
            </code>
          </span>
        </div>
        <div className="evidence-badges" role="group" aria-label="Trạng thái kiểm chứng">
          <span
            className={`evidence-badge ${resMeta.badgeClass}`}
            title={resMeta.description}
            role="status"
          >
            <span aria-hidden="true" className="badge-icon">
              {resMeta.indicator}
            </span>
            <span>{resMeta.label}</span>
          </span>
          <span
            className={`evidence-badge ${supMeta.badgeClass}`}
            title={supMeta.description}
            role="status"
          >
            <span aria-hidden="true" className="badge-icon">
              {supMeta.indicator}
            </span>
            <span>{supMeta.label}</span>
          </span>
        </div>
      </div>

      <div className="evidence-meta muted">
        <span>
          Symbol: <strong>{item.symbol ?? '—'}</strong>
        </span>
        <span aria-hidden="true">·</span>
        <span>
          Commit:{' '}
          <code title={item.commit}>
            {item.commit.length > 10 ? `${item.commit.slice(0, 10)}…` : item.commit}
          </code>
        </span>
        {item.snapshotId && (
          <>
            <span aria-hidden="true">·</span>
            <span>
              Snapshot:{' '}
              <code title={item.snapshotId}>{item.snapshotId.slice(0, 8)}…</code>
            </span>
          </>
        )}
      </div>

      {item.verificationReason && (
        <div className="evidence-issue" role="note">
          <span className="evidence-issue-label">Lý do kiểm chứng:</span>{' '}
          <code>{item.verificationReason}</code>
        </div>
      )}

      {item.excerpt && (
        <pre className="evidence-excerpt" aria-label="Đoạn trích dẫn mã nguồn">
          {item.excerpt}
        </pre>
      )}
    </article>
  )
}

