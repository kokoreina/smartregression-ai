import { useSyncExternalStore } from 'react'

export type ThemePreference = 'light' | 'dark' | 'system'
const storageKey = 'smartregression.theme'
const listeners = new Set<() => void>()
let detach: (() => void) | undefined

function preference(value: string | null | undefined): ThemePreference {
  return value === 'light' || value === 'dark' ? value : 'system'
}

function currentPreference(): ThemePreference {
  if (typeof document === 'undefined') return 'system'
  if (document.documentElement.dataset.themePreference) return preference(document.documentElement.dataset.themePreference)
  try { return preference(localStorage.getItem(storageKey)) } catch { return 'system' }
}

function snapshot() {
  const resolved = typeof document !== 'undefined' && document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
  return `${currentPreference()}:${resolved}`
}

function apply(value: ThemePreference) {
  const root = document.documentElement
  const dark = value === 'dark' || (value === 'system' && matchMedia('(prefers-color-scheme: dark)').matches)
  root.classList.add('theme-switching')
  root.dataset.themePreference = value
  root.dataset.theme = dark ? 'dark' : 'light'
  root.style.colorScheme = dark ? 'dark' : 'light'
  document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')?.setAttribute('content', dark ? '#10151e' : '#f4f6f8')
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove('theme-switching')))
  listeners.forEach(listener => listener())
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  if (listeners.size === 1) {
    const media = matchMedia('(prefers-color-scheme: dark)')
    const systemChanged = () => { if (currentPreference() === 'system') apply('system') }
    const storageChanged = (event: StorageEvent) => { if (event.key === storageKey || event.key === null) apply(preference(event.newValue)) }
    media.addEventListener('change', systemChanged)
    window.addEventListener('storage', storageChanged)
    detach = () => { media.removeEventListener('change', systemChanged); window.removeEventListener('storage', storageChanged) }
    apply(currentPreference())
  }
  return () => { listeners.delete(listener); if (!listeners.size) { detach?.(); detach = undefined } }
}

export function setThemePreference(value: ThemePreference) {
  try { localStorage.setItem(storageKey, value) } catch { /* Keep the current tab usable without persistence. */ }
  apply(value)
}

export function useTheme() {
  const value = useSyncExternalStore(subscribe, snapshot, () => 'system:light')
  return { preference: value.split(':')[0], resolved: value.split(':')[1] }
}

export function ThemeController() { useTheme(); return null }
