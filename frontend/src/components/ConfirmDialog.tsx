import { useEffect, useRef } from 'react'

export function ConfirmDialog({ open, title, children, confirmLabel, onConfirm, onClose }: {
  open: boolean; title: string; children: React.ReactNode; confirmLabel: string
  onConfirm: () => void; onClose: () => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const previousFocus = useRef<HTMLElement | null>(null)
  useEffect(() => {
    const node = dialog.current
    if (open && node && !node.open) {
      previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null
      node.showModal()
      node.querySelector<HTMLButtonElement>('[data-dialog-cancel]')?.focus()
    }
    if (!open) {
      if (node?.open) node.close()
      if (previousFocus.current?.isConnected) previousFocus.current.focus()
      previousFocus.current = null
    }
  }, [open])
  function keyboard(event: React.KeyboardEvent<HTMLDialogElement>) {
    if (event.key !== 'Tab') return
    const node = dialog.current
    const buttons = node?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')
    if (!node || !buttons?.length) return
    const first = buttons[0]; const last = buttons[buttons.length - 1]
    if (event.shiftKey && (document.activeElement === first || !node.contains(document.activeElement))) { event.preventDefault(); last?.focus() }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
  }
  return <dialog ref={dialog} className="confirm-dialog" aria-labelledby="confirm-title" onCancel={onClose} onClose={onClose} onKeyDown={keyboard}>
    <h2 id="confirm-title">{title}</h2><p>{children}</p><div className="dialog-actions">
      <button type="button" onClick={onClose} autoFocus data-dialog-cancel>Hủy</button>
      <button type="button" className="primary-button" onClick={onConfirm}>{confirmLabel}</button>
    </div>
  </dialog>
}
