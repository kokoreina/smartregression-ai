import { useId, useState } from 'react'
import type { components } from '../../types/generated'
import './dashboardCharts.css'

type Summary = components['schemas']['Dashboard']
const names: Record<string, string> = { queued: 'Đang chờ', running: 'Đang phân tích', completed: 'Đã kết thúc phân tích', failed: 'Phân tích lỗi', interrupted: 'Bị gián đoạn', not_run: 'Chưa chạy' }

function calendarDate(value: string, timezone: string) {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date(value))
  const part = (type: string) => parts.find(item => item.type === type)?.value
  return `${part('year')}-${part('month')}-${part('day')}`
}

function dailySeries(summary: Summary) {
  const { start, end, timezone } = summary.filters
  const first = calendarDate(start, timezone)
  // Reporting uses an exclusive end; calendar iteration in UTC avoids DST jumps.
  const last = calendarDate(new Date(new Date(end).getTime() - 1).toISOString(), timezone)
  const series: [string, number][] = []
  for (let time = Date.parse(`${first}T00:00:00Z`); time <= Date.parse(`${last}T00:00:00Z`); time += 86400000) {
    const day = new Date(time).toISOString().slice(0, 10)
    series.push([day, summary.daily_runs[day] ?? 0])
  }
  return series
}

function shortDate(day: string) { return `${day.slice(8, 10)}/${day.slice(5, 7)}` }

function ActivityChart({ summary }: { summary: Summary }) {
  const id = useId()
  const series = dailySeries(summary)
  const [selected, setSelected] = useState<number | null>(null)
  const index = Math.min(selected ?? series.length - 1, series.length - 1)
  const current = series[index]
  const maximum = Math.max(1, ...series.map(([, count]) => count))
  const x = (i: number) => 38 + (series.length > 1 ? i / (series.length - 1) : .5) * 624
  const y = (count: number) => 186 - count / maximum * 146
  const ticks = [...new Set([0, Math.floor((series.length - 1) / 2), series.length - 1])]
  const columns = series.length <= 12
  return <section className="auth-card dashboard-chart activity-chart" aria-labelledby={`${id}-title`}>
    <div className="chart-heading"><div><p className="chart-eyebrow">HOẠT ĐỘNG PHÂN TÍCH</p><h2 id={`${id}-title`}>Lượt phân tích theo ngày</h2></div><span className="chart-total">{summary.total_runs.toLocaleString('vi-VN')}<small>lượt trong bộ lọc</small></span></div>
    <p className="chart-description">Theo ngày bắt đầu · múi giờ {summary.filters.timezone}. Ngày không có lượt được ghi là 0.</p>
    {summary.total_runs > 0 && current ? <>
      <p className="chart-readout" aria-live="polite"><time dateTime={current[0]}>{shortDate(current[0])}/{current[0].slice(0, 4)}</time><strong>{current[1].toLocaleString('vi-VN')} lượt phân tích</strong></p>
      <svg className="activity-plot" viewBox="0 0 700 225" role="img" aria-label={`Lượt phân tích theo ngày, tổng ${summary.total_runs} lượt. Số liệu chi tiết ở bảng bên dưới.`}
        onPointerDown={event => { const bounds = event.currentTarget.getBoundingClientRect(); const position = (event.clientX - bounds.left) / bounds.width * 700; setSelected(Math.max(0, Math.min(series.length - 1, Math.round((position - 38) / 624 * (series.length - 1))))) }}>
        <line x1="20" x2="680" y1="186" y2="186" className="chart-baseline" />
        {columns ? series.map(([day, count], i) => <g key={day}><rect x={x(i) - 16} y={y(count)} width="32" height={count ? 186 - y(count) : 0} rx="4" className="chart-column" /><text x={x(i)} y={y(count) - 10} textAnchor="middle" className="chart-value">{count}</text></g>) : <><polyline points={series.map(([, count], i) => `${x(i)},${y(count)}`).join(' ')} className="chart-line" /><line x1={x(index)} x2={x(index)} y1="24" y2="186" className="chart-selection" /><circle cx={x(index)} cy={y(current[1])} r="5" className="chart-point" /></>}
        {(columns ? series.map((_, i) => i) : ticks).map(i => { const day = series[i]; return day ? <text key={i} x={x(i)} y="216" textAnchor="middle" className="chart-date">{shortDate(day[0])}</text> : null })}
      </svg>
      <label className="chart-day-picker" htmlFor={`${id}-day`}>Xem từng ngày<input id={`${id}-day`} type="range" min="0" max={series.length - 1} value={index} onChange={event => setSelected(Number(event.target.value))} aria-valuetext={`${current[0]}: ${current[1]} lượt phân tích`} /></label>
      <details className="chart-data"><summary>Xem bảng số liệu</summary><div className="table-scroll" tabIndex={0} role="region" aria-label="Số lượt phân tích từng ngày"><table><caption>Lượt phân tích theo ngày ({summary.filters.timezone})</caption><thead><tr><th scope="col">Ngày</th><th scope="col">Lượt phân tích</th></tr></thead><tbody>{series.map(([day, count]) => <tr key={day}><th scope="row">{day}</th><td>{count}</td></tr>)}</tbody></table></div></details>
    </> : <ChartEmpty text="Chưa có lượt phân tích trong khoảng thời gian này." />}
  </section>
}

function ChartEmpty({ text }: { text: string }) {
  return <div className="chart-empty"><svg viewBox="0 0 100 50" aria-hidden="true"><path d="M8 42H92M18 34V24M39 34V14M60 34V20M81 34V8" /></svg><p>{text}</p><small>Chạy phân tích trong dự án rồi cập nhật tổng quan.</small></div>
}

function StatusChart({ values, ai = false }: { values: Record<string, number>; ai?: boolean }) {
  const id = useId()
  const entries = Object.entries(values).sort((a, b) => b[1] - a[1])
  const total = entries.reduce((sum, [, count]) => sum + count, 0)
  return <section className="auth-card dashboard-chart status-chart" aria-labelledby={id}>
    <p className="chart-eyebrow">{ai ? 'HỖ TRỢ AI' : 'PHÂN TÍCH TĨNH'}</p><h2 id={id}>{ai ? 'Trạng thái AI của lượt phân tích' : 'Phân bố trạng thái tĩnh'}</h2>
    <p className="chart-description">{ai ? 'Chưa chạy AI được hiển thị riêng; không đồng nghĩa với lỗi.' : 'Trạng thái xử lý phân tích, không phải kết quả pass/fail của test.'}</p>
    {total ? <ul className="status-chart-list">{entries.map(([key, count]) => <li key={key}>
      <div className="status-chart-label"><span>{ai && key === 'completed' ? 'Đã chạy AI' : ai && key === 'running' ? 'AI đang chạy' : ai && key === 'failed' ? 'AI lỗi' : names[key] ?? key}</span><strong>{count.toLocaleString('vi-VN')}<small>{(count / total * 100).toLocaleString('vi-VN', { maximumFractionDigits: 1 })}%</small></strong></div>
      <div className="status-chart-track" aria-hidden="true"><span className={`chart-status-${key}`} style={{ width: `${count / total * 100}%` }} /></div>
    </li>)}</ul> : <ChartEmpty text="Chưa có trạng thái để tổng hợp." />}
  </section>
}

export function DashboardCharts({ summary }: { summary: Summary }) {
  return <div className="dashboard-visualizations"><ActivityChart key={summary.snapshot_id} summary={summary} /><div className="dashboard-status-charts"><StatusChart values={summary.static_statuses} /><StatusChart values={summary.ai_statuses} ai /></div></div>
}
