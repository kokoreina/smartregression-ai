import { createContext, useContext } from 'react'
import type { CurrentUser } from './authClient'

export type SessionState =
  | { kind: 'loading' }
  | { kind: 'guest' }
  | { kind: 'unavailable'; message: string }
  | { kind: 'user'; user: CurrentUser }

export const AuthContext = createContext<{
  state: SessionState
  accept: (user: CurrentUser) => void
  refresh: () => Promise<void>
  clear: () => void
} | null>(null)

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider required')
  return value
}
