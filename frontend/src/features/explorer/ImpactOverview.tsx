import { useId, useState } from 'react'
import type { components } from '../../types/generated'
import './impactOverview.css'
import { CoverageDetails } from './CoverageDetails'

type Impact = components['schemas']['ImpactSummary']
const groups = [['changed', 'File thay đổi'], ['direct', 'Ảnh hưởng trực tiếp'], ['indirect', 'Ảnh hưởng gián tiếp']] as const

export function ImpactOverview({ value, onChoose, title = 'Ảnh hưởng tiềm năng theo phân tích tĩnh' }: { value: Impact; onChoose?: (path: string) => void; title?: string }) {
  const id = useId()
  const [chosen, setChosen] = useState('')
  const targets = [...value.direct, ...value.indirect].filter(path => (value.paths[path]?.length ?? 0) > 1)
  const target = targets.includes(chosen) ? chosen : targets[0]
  const chain = target ? value.paths[target] : null
  return <section className="impact-overview" aria-labelledby={`${id}-heading`}>
    <h3 id={`${id}-heading`}>{title}</h3>
    <p className="impact-overview-intro">So với {value.denominator == null ? 'số file chưa xác định' : `${value.denominator} file phân tích được`} trong snapshot.</p>
    <dl className="impact-comparison">{groups.map(([key, label]) => {
      const count = value.counts[key]
      const percentage = value.percentages[key]
      return <div key={key} className={`impact-comparison-row impact-group-${key}`}><dt>{label}</dt><dd><strong>{count == null ? 'Chưa đo' : `${count} file`}</strong><span>{percentage == null ? 'Chưa có tỷ lệ' : `${percentage}%`}</span></dd>
        {percentage != null && <div className="impact-comparison-track" aria-hidden="true"><span style={{ width: `${Math.max(0, Math.min(100, percentage))}%` }} /></div>}
      </div>
    })}</dl>
    <p className="impact-overview-note">Ảnh hưởng tiềm năng theo quan hệ tĩnh; tỷ lệ không phải xác suất gây lỗi.</p>
    {(value.coverage.status !== 'complete' || value.unresolved_count > 0 || value.unknown_changed_count > 0) && <div className="impact-coverage-note"><strong>Giới hạn chung của snapshot</strong><p>{value.unresolved_count} quan hệ chưa giải được · {value.coverage.unsupported_files.length} file ngoài phạm vi{value.unknown_changed_count ? ` · ${value.unknown_changed_count} file thay đổi chưa phân tích được` : ''}.</p><p>Đây là số tổng của snapshot, không phải số lỗi của file đang chọn.</p><details><summary>Giải thích phạm vi và nguyên nhân</summary><CoverageDetails coverage={value.coverage} unresolvedCount={value.unresolved_count} compact /></details></div>}
    {chain && <details className="impact-propagation" open><summary>Đường lan truyền ảnh hưởng</summary>
      <label htmlFor={`${id}-target`}>File cần đối chiếu</label><select id={`${id}-target`} value={target} onChange={event => setChosen(event.target.value)}>{targets.map(path => <option value={path} key={path}>{path}</option>)}</select>
      <ol aria-label="Chuỗi lan truyền ảnh hưởng">{chain.map((path, index) => <li key={`${path}-${index}`}><span className="impact-path-step" aria-hidden="true">{index + 1}</span>{onChoose ? <button type="button" onClick={() => onChoose(path)}>{path}</button> : <code>{path}</code>}</li>)}</ol>
      <p>Chiều lan truyền từ file thay đổi tới file sử dụng nó, ngược chiều import. Đây là một đường tĩnh quan sát được, không phải luồng chạy thực tế.</p>
    </details>}
    {value.paths_truncated && <p className="impact-overview-note">Đường lan truyền đã giới hạn; số tổng phía trên vẫn giữ nguyên.</p>}
  </section>
}
