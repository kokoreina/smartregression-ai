import { useId } from 'react'
import type { components } from '../../types/generated'
import './coverageDetails.css'

type Coverage = components['schemas']['GraphCoverage']
const reasons: Record<string, string> = {
  unresolved_internal_import: 'Import nội bộ chưa tìm được đích',
  external_or_unresolved_import: 'Import bên ngoài hoặc chưa xác định dependency',
  unresolved_static_call: 'Lời gọi chưa xác định được đích',
  shadowed_call: 'Lời gọi qua tham số/biến chưa xác định hoặc bị gán lại',
  dynamic_or_shadowed_call: 'Biểu thức gọi động hoặc phức hợp',
  unsupported_scope_call: 'Lời gọi trong lambda/comprehension chưa hỗ trợ',
  ambiguous_symbol: 'Tên symbol có nhiều định nghĩa',
  wildcard_import: 'Import dấu * chưa xác định đủ tên',
  python_parse_error: 'Lỗi đọc cú pháp Python',
  source_limit: 'File vượt giới hạn đọc cú pháp',
  shadowed_import: 'Import có tên bị ghi đè',
  dynamic_call: 'Lời gọi JavaScript động', dynamic_import: 'Import JavaScript động',
  dynamic_require: 'Require có đường dẫn động',
}
const fileKinds: Record<string, string> = {
  documentation_asset: 'Tài liệu và tài nguyên', configuration: 'Cấu hình/dependency',
  other_unsupported: 'Loại file khác chưa hỗ trợ', excluded: 'File bị loại khỏi nguồn đọc',
}
const classified: Record<string, string> = {
  builtin_call: 'Lời gọi built-in Python nhận diện được',
  stdlib_call: 'Lời gọi qua thư viện chuẩn ngoài graph nội bộ',
  stdlib_import: 'Import thư viện chuẩn nhận diện được',
}

export function CoverageDetails({ coverage, unresolvedCount, compact = false }: { coverage: Coverage; unresolvedCount?: number; compact?: boolean }) {
  const id = useId()
  const Heading = compact ? 'h4' : 'h2'
  const diagnostics = coverage.diagnostics
  const unresolved = diagnostics ? Object.values(diagnostics.unresolved_by_reason).reduce((sum, count) => sum + count, 0) : unresolvedCount
  return <section className={`coverage-details${compact ? ' is-compact' : ''}`} aria-labelledby={`${id}-title`}>
    <Heading id={`${id}-title`}>Phạm vi phân tích của snapshot</Heading>
    <dl className="coverage-file-counts"><div><dt>File đọc được cú pháp</dt><dd>{coverage.analyzed_files.length}</dd></div><div><dt>File không đọc được cú pháp</dt><dd>{coverage.unparsed_files.length}</dd></div><div><dt>File ngoài phạm vi đọc mã</dt><dd>{coverage.unsupported_files.length}</dd></div></dl>
    <p>Đọc được cú pháp chưa có nghĩa đã xác định hết quan hệ trong file. Kết quả ảnh hưởng hiện dựa trên import nội bộ; call graph là thông tin bổ sung.</p>
    <details><summary>{unresolved == null ? coverage.status === 'partial' ? 'Vì sao snapshot còn giới hạn?' : 'Chi tiết về quan hệ và phạm vi' : `${unresolved.toLocaleString('vi-VN')} trường hợp chưa xác định · xem nguyên nhân`}</summary>
      <p>Số này đếm các lần xuất hiện trên toàn snapshot, không phải số lỗi của file đang chọn hay số hàm duy nhất.</p>
      {diagnostics ? <>
        {Object.keys(diagnostics.unresolved_by_reason).length ? <dl className="coverage-reasons">{Object.entries(diagnostics.unresolved_by_reason).map(([reason, count]) => <div key={reason}><dt>{reasons[reason] ?? reason}</dt><dd>{count.toLocaleString('vi-VN')}</dd></div>)}</dl> : <p>Không còn trường hợp chưa xác định được trong các loại quan hệ đang hỗ trợ. Đây không phải xác nhận an toàn của chương trình.</p>}
        {Object.keys(diagnostics.classified_by_kind).length > 0 && <><h4>Được nhận diện riêng, không gộp vào phần chưa biết</h4><dl className="coverage-reasons">{Object.entries(diagnostics.classified_by_kind).map(([kind, count]) => <div key={kind}><dt>{classified[kind] ?? kind}</dt><dd>{count.toLocaleString('vi-VN')}</dd></div>)}</dl><p>Các tham chiếu này không được biến thành cạnh gọi nội bộ. Không có thư viện hoặc mã nguồn đầu vào nào được chạy để phân tích.</p></>}
      </> : <p>Snapshot cũ chưa có phân loại chi tiết. Mở lại phiên bản bằng bộ phân tích hiện tại để cập nhật; không suy đoán nguyên nhân từ số tổng.</p>}
    </details>
    {(coverage.unparsed_files.length > 0 || coverage.unsupported_files.length > 0) && <details><summary>File nào chưa được phân tích?</summary>
      {coverage.unparsed_files.length > 0 && <><h4>Không đọc được cú pháp</h4><ul>{coverage.unparsed_files.map(path => <li key={path}><code>{path}</code></li>)}</ul></>}
      {diagnostics ? Object.entries(diagnostics.file_groups).map(([kind, paths]) => <details key={kind}><summary>{fileKinds[kind] ?? kind} ({paths.length})</summary><ul>{paths.map(path => <li key={path}><code>{path}</code></li>)}</ul></details>) : <ul>{coverage.unsupported_files.map(path => <li key={path}><code>{path}</code></li>)}</ul>}
      <p>Nhóm file dựa trên tên/phần mở rộng. Tài liệu và ảnh không tham gia graph mã nguồn; cấu hình pytest, CI và dependency vẫn có thể thay đổi cách chạy test.</p>
      {!!diagnostics?.excluded_files?.length && <p>{diagnostics.excluded_files.length} file trong các nhóm trên còn bị loại bởi chính sách đọc nguồn (loại file, nội dung hoặc giới hạn hỗ trợ). Việc phân nhóm không mở lại quyền đọc các file này.</p>}
    </details>}
    <p className="coverage-boundary">Giới hạn hiển thị 150 node là giới hạn của khung graph, tách biệt với phạm vi phân tích. Không có cạnh quan sát được không đồng nghĩa với không có ảnh hưởng.</p>
  </section>
}
