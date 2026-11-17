import { useEffect, useRef, useState } from 'react'
import type { components } from '../../types/generated'
import { AccountError, productRequest } from '../auth/authClient'

type State = components['schemas']['ViewState']
type Input = components['schemas']['ViewStateInput']

export function ResumeState({ projectId, value, ready, restore, onLoaded }: { projectId: string; value: Omit<Input, 'version'>; ready: boolean; restore: (value: State) => void; onLoaded?: (saved: State | null | undefined) => void }) {
  const [loaded, setLoaded] = useState(false)
  const [notice, setNotice] = useState('')
  const version = useRef(0)
  const onRestore = useRef(restore)
  const onReady = useRef(onLoaded)
  const lastSaved = useRef('')
  const pending = useRef<Omit<Input, 'version'> | null>(null)
  const flight = useRef(false)
  const active = useRef(true)
  const conflict = useRef(false)
  useEffect(() => { onRestore.current = restore; onReady.current = onLoaded }, [restore, onLoaded])
  useEffect(() => {
    active.current = true
    productRequest<State | null>(`/projects/${projectId}/view-state`).then(saved => {
      if (!active.current) return
      if (saved) { version.current = saved.version; onRestore.current(saved) }
      setLoaded(true)
      onReady.current?.(saved)
    }).catch(() => { if (active.current) { setNotice('Chưa đọc được vị trí đã lưu. Bạn vẫn có thể khám phá bằng liên kết.'); onReady.current?.(undefined) } })
    return () => { active.current = false }
  }, [projectId])
  const serialized = JSON.stringify(value)
  useEffect(() => {
    if (!loaded || !ready || conflict.current) return
    pending.current = JSON.parse(serialized) as Omit<Input, 'version'>
    async function flush() {
      if (flight.current || !pending.current || conflict.current || !active.current) return
      const input = pending.current
      const text = JSON.stringify(input)
      if (text === lastSaved.current) { pending.current = null; return }
      pending.current = null; flight.current = true; setNotice('Đang lưu vị trí…')
      try {
        const saved = await productRequest<State>(`/projects/${projectId}/view-state`, 'PUT', { ...input, version: version.current })
        version.current = saved.version; lastSaved.current = text
        if (active.current) setNotice('Đã lưu vị trí khám phá.')
      } catch (cause) {
        conflict.current = true
        if (active.current) setNotice(cause instanceof AccountError && cause.code === 'version_conflict' ? 'Vị trí đã thay đổi ở phiên khác. Tải lại trang để tiếp tục lưu; lựa chọn hiện tại chưa bị ghi đè.' : 'Chưa lưu được vị trí. Tải lại để kết nối lại; không tự gửi lặp.')
      } finally {
        flight.current = false
        if (active.current && pending.current && !conflict.current) window.setTimeout(() => void flush(), 1000)
      }
    }
    const timer = window.setTimeout(() => void flush(), 1000)
    return () => window.clearTimeout(timer)
  }, [loaded, ready, serialized, projectId])
  return notice ? <p role="status" className="field-hint">{notice}</p> : null
}
