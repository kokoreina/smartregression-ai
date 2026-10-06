import type { ReactNode } from 'react'

export function Notice({ children, error = false }: { children: ReactNode; error?: boolean }) {
  return <p className={`notice ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}>{children}</p>
}
