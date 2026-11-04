import { useEffect, useRef, useState } from 'react'
import { Notice } from '../components/Notice'
import { loadDemo, type AnalysisReport } from '../features/reports/demo'
import { ReportView } from '../features/reports/ReportView'
import {
  loadStageReportFixture,
  loadStageReportFromFile,
  type ReportLoadState,
  type StageAnalysisReport,
} from '../features/reports/stageReport'
import { StageReportView } from '../features/reports/StageReportView'
import { checkHealth } from '../lib/api'

type AppMode = 'demo-v1' | 'stage-v2'

export function App() {
  const [attempt, setAttempt] = useState(0)
  const [health, setHealth] = useState('Đang kết nối API…')

  // Legacy demo v1
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [legacyLoading, setLegacyLoading] = useState(true)
  const [legacyError, setLegacyError] = useState('')

  // Stage report v2
  const [mode, setMode] = useState<AppMode>('demo-v1')
  const [stageState, setStageState] = useState<ReportLoadState>({ kind: 'idle' })
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Health check
  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), 5000)
    let active = true
    checkHealth(controller.signal)
      .then(() => { if (active) setHealth('API đã kết nối · chỉ trạng thái dịch vụ') })
      .catch(() => { if (active) setHealth('API chưa kết nối · vẫn xem được DEMO') })
      .finally(() => window.clearTimeout(timer))
    return () => { active = false; controller.abort(); window.clearTimeout(timer) }
  }, [attempt])

  // Load legacy DEMO v1
  useEffect(() => {
    if (mode !== 'demo-v1') return
    let active = true
    loadDemo()
      .then((data) => { if (active) setReport(data) })
      .catch(() => { if (active) setLegacyError('Không tải được report DEMO. Vui lòng tải lại trang.') })
      .finally(() => { if (active) setLegacyLoading(false) })
    return () => { active = false }
  }, [mode])

  function handleLoadFixture(variant: 'partial' | 'empty' | 'failed' | 'not-implemented') {
    setMode('stage-v2')
    setStageState({ kind: 'loading' })
    loadStageReportFixture(variant)
      .then((r) => setStageState({ kind: 'loaded', report: r }))
      .catch((e: unknown) =>
        setStageState({ kind: 'error', message: e instanceof Error ? e.message : 'Lỗi không xác định.' }),
      )
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    // Reset input so the same file can be loaded again
    e.target.value = ''
    setMode('stage-v2')
    setStageState({ kind: 'loading' })
    loadStageReportFromFile(file)
      .then((r) => setStageState({ kind: 'loaded', report: r }))
      .catch((err: unknown) =>
        setStageState({ kind: 'error', message: err instanceof Error ? err.message : 'Lỗi không xác định.' }),
      )
  }

  function handleBackToDemo() {
    setMode('demo-v1')
    setStageState({ kind: 'idle' })
  }

  const stageReport =
    stageState.kind === 'loaded' ? (stageState.report as StageAnalysisReport) : null

  return (
    <>
      <header>
        <a className="brand" href="/">SR<span>SmartRegression AI</span></a>
        <span className="tag">RESEARCH BOOTSTRAP</span>
      </header>
      <main>
        <div className="intro">
          <p className="eyebrow">CHANGE IMPACT / REGRESSION TEST SELECTION</p>
          <h1>Hiểu thay đổi.<br /><span>Kiểm thử có bằng chứng.</span></h1>
          <p>Khung báo cáo cho nhóm nghiên cứu SmartRegression AI.</p>
        </div>

        {/* API health */}
        <div className="connection">
          <span role="status">{health}</span>
          <button onClick={() => { setHealth('Đang kết nối API…'); setAttempt((n) => n + 1) }}>
            Kiểm tra lại API
          </button>
        </div>

        {/* Report loader toolbar */}
        <div className="report-toolbar" role="toolbar" aria-label="Mở báo cáo">
          <span className="label" style={{ alignSelf: 'center' }}>Mở báo cáo:</span>
          <button onClick={handleBackToDemo} aria-pressed={mode === 'demo-v1'}>DEMO v1</button>
          <button onClick={() => handleLoadFixture('partial')}>Fixture: partial</button>
          <button onClick={() => handleLoadFixture('empty')}>Fixture: empty</button>
          <button onClick={() => handleLoadFixture('failed')}>Fixture: failed</button>
          <button onClick={() => handleLoadFixture('not-implemented')}>Fixture: not-implemented</button>
          <button
            onClick={() => fileInputRef.current?.click()}
            aria-label="Mở file JSON báo cáo từ máy tính"
          >
            Mở file JSON…
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            aria-hidden="true"
            tabIndex={-1}
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
        </div>

        {/* Content area */}
        {mode === 'demo-v1' && (
          <>
            <Notice><strong>DEMO — dữ liệu minh họa viết tay.</strong> Chưa phân tích repository, chưa gọi LLM và chưa chạy test.</Notice>
            {legacyLoading && <Notice>Đang tải report minh họa…</Notice>}
            {legacyError && <Notice error>{legacyError}</Notice>}
            {!legacyLoading && !legacyError && !report && <Notice>Chưa có report.</Notice>}
            {report && <ReportView report={report} />}
          </>
        )}

        {mode === 'stage-v2' && (
          <>
            {stageState.kind === 'loading' && <Notice>Đang tải báo cáo…</Notice>}
            {stageState.kind === 'error' && (
              <Notice error>
                <strong>Báo cáo không hợp lệ:</strong> {stageState.message}
              </Notice>
            )}
            {stageState.kind === 'idle' && <Notice>Chọn fixture hoặc mở file JSON để xem báo cáo.</Notice>}
            {stageReport && (
              <>
                {stageReport.data_kind === 'demo' && (
                  <Notice><strong>DEMO — fixture minh họa.</strong> Dữ liệu đánh nhãn DEMO, không phải kết quả phân tích thật.</Notice>
                )}
                <StageReportView report={stageReport} />
              </>
            )}
          </>
        )}

        <footer>SmartRegression AI · Bootstrap 0.1 · Test thất bại không tự xác nhận một fault.</footer>
      </main>
    </>
  )
}
