import { useEffect, useId, useRef } from 'react'
import './confirmDialog.css'

export function ConfirmDialog({ open, title, children, confirmLabel, onConfirm, onClose, appearance = 'default' }: {
  open: boolean; title: string; children: React.ReactNode; confirmLabel: string
  onConfirm: () => void; onClose: () => void
  appearance?: 'default' | 'signout'
}) {
  const id = useId()
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
  return <dialog ref={dialog} className={`confirm-dialog${appearance === 'signout' ? ' confirm-signout' : ''}`} aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} onCancel={onClose} onClose={onClose} onKeyDown={keyboard}>
    {appearance === 'signout' && <div className="confirm-signout-heading"><span className="confirm-signout-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5M14 8l4 4-4 4M8 12h10" /></svg></span><button type="button" className="confirm-dismiss" aria-label="Đóng hộp xác nhận" onClick={onClose}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6" /></svg></button></div>}
    <h2 id={`${id}-title`}>{title}</h2><p id={`${id}-description`}>{children}</p><div className="dialog-actions">
      <button type="button" onClick={onClose} autoFocus data-dialog-cancel>{appearance === 'signout' ? 'Ở lại' : 'Hủy'}</button>
      <button type="button" className={appearance === 'signout' ? 'confirm-signout-action' : 'primary-button'} onClick={onConfirm}>{confirmLabel}</button>
    </div>
  </dialog>
}
