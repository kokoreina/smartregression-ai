/**
 * Task 2.18: Loader and runtime validator cho StageAnalysisReport (v2).
 *
 * Phân biệt rõ DEMO vs real, validate contract tại runtime, không cast ngầm.
 * Không gọi API mới — cách load cụ thể thống nhất với contract/use case.
 */
import type { components } from '../../types/generated'
import schema from '../../../../contracts/generated/openapi.json'
import { readReportFile, validateReportValue } from './stageReportValidation'

export type StageAnalysisReport = components['schemas']['StageAnalysisReport']
export type StageStatus = components['schemas']['StageAnalysisReport']['analysis_status']

export type ReportLoadState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'loaded'; report: StageAnalysisReport }

/** Validate một đối tượng JSON là StageAnalysisReport hợp lệ tại runtime */
export function validateStageReport(raw: unknown): StageAnalysisReport {
  validateReportValue(raw, schema.components.schemas)
  return raw
}

/** Load một StageAnalysisReport từ File do người dùng chọn */
export async function loadStageReportFromFile(file: File): Promise<StageAnalysisReport> {
  return readReportFile(file, schema.components.schemas)
}

/** Load StageAnalysisReport từ fixture JSON (bundled, đánh nhãn DEMO) */
export async function loadStageReportFixture(
  variant: 'partial' | 'empty' | 'failed' | 'not-implemented',
): Promise<StageAnalysisReport> {
  const loader = {
    partial: () => import('../../../../examples/reports/stage-report.partial.json'),
    empty: () => import('../../../../examples/reports/stage-report.empty.json'),
    failed: () => import('../../../../examples/reports/stage-report.failed.json'),
    'not-implemented': () =>
      import('../../../../examples/reports/stage-report.not-implemented.json'),
  }[variant]
  const { default: fixture } = await loader()
  return validateStageReport(fixture)
}

/** Giải thích analysis_status thành nhãn tiếng Việt */
export function statusLabel(status: StageStatus): string {
  switch (status) {
    case 'completed':
      return 'Hoàn tất'
    case 'partial':
      return 'Một phần'
    case 'failed':
      return 'Thất bại'
    case 'not_run':
      return 'Chưa chạy'
    case 'not_implemented':
      return 'Chưa triển khai'
  }
}

/** Trả về class CSS tương ứng với analysis_status */
export function statusClass(status: StageStatus): string {
  switch (status) {
    case 'completed':
      return 'status-completed'
    case 'partial':
      return 'status-partial'
    case 'failed':
      return 'status-failed'
    case 'not_run':
      return 'status-not-run'
    case 'not_implemented':
      return 'status-not-implemented'
  }
}
