import { useEffect, useState } from 'react'
import { Notice } from '../components/Notice'
import { loadDemo, type AnalysisReport } from '../features/reports/demo'
import { ReportView } from '../features/reports/ReportView'
import { checkHealth } from '../lib/api'

export function App() {
  const [attempt, setAttempt] = useState(0)
  const [health, setHealth] = useState('Đang kết nối API…')
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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

  useEffect(() => {
    let active = true
    loadDemo()
      .then((data) => { if (active) setReport(data) })
      .catch(() => { if (active) setError('Không tải được report DEMO. Vui lòng tải lại trang.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  return <>
    <header><a className="brand" href="/">SR<span>SmartRegression AI</span></a><span className="tag">RESEARCH BOOTSTRAP</span></header>
    <main>
      <div className="intro"><p className="eyebrow">CHANGE IMPACT / REGRESSION TEST SELECTION</p>
        <h1>Hiểu thay đổi.<br /><span>Kiểm thử có bằng chứng.</span></h1>
        <p>Khung báo cáo cho nhóm nghiên cứu SmartRegression AI.</p>
      </div>
      <div className="connection"><span role="status">{health}</span><button onClick={() => { setHealth('Đang kết nối API…'); setAttempt((n) => n + 1) }}>Kiểm tra lại API</button></div>
      <Notice><strong>DEMO — dữ liệu minh họa viết tay.</strong> Chưa phân tích repository, chưa gọi LLM và chưa chạy test.</Notice>
      {loading && <Notice>Đang tải report minh họa…</Notice>}
      {error && <Notice error>{error}</Notice>}
      {!loading && !error && !report && <Notice>Chưa có report.</Notice>}
      {report && <ReportView report={report} />}
      <footer>SmartRegression AI · Bootstrap 0.1 · Test thất bại không tự xác nhận một fault.</footer>
    </main>
  </>
}
