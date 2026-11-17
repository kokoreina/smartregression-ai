import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { accountApi, AccountError, clearAuthClient, type CurrentUser } from './authClient'
import { AuthContext, type SessionState } from './authContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({ kind: 'loading' })
  const sequence = useRef(0)
  const mounted = useRef(false)
  const clear = useCallback(() => {
    ++sequence.current
    clearAuthClient()
    setState({ kind: 'guest' })
  }, [])
  const accept = useCallback((user: CurrentUser) => {
    ++sequence.current
    setState({ kind: 'user', user })
  }, [])
  const refresh = useCallback(() => {
    const current = ++sequence.current
    return accountApi.me().then(user => {
      if (mounted.current && current === sequence.current) setState({ kind: 'user', user })
    }).catch((error: unknown) => {
      if (mounted.current && current === sequence.current) setState(error instanceof AccountError && error.status === 401
        ? { kind: 'guest' } : { kind: 'unavailable', message: error instanceof Error ? error.message : 'Không đọc được phiên.' })
    })
  }, [])
  useEffect(() => {
    mounted.current = true
    void refresh()
    window.addEventListener('sr:session-expired', clear)
    return () => { mounted.current = false; window.removeEventListener('sr:session-expired', clear) }
  }, [refresh, clear])
  return <AuthContext.Provider value={{ state, clear, accept, refresh }}>{children}</AuthContext.Provider>
}
