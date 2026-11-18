import { setThemePreference, useTheme } from '../app/theme'
import { WorkspaceIcon } from './WorkspaceIcon'

export function ThemeToggle() {
  const theme = useTheme()
  const next = theme.resolved === 'dark' ? 'light' : 'dark'
  const label = `Chuyển sang giao diện ${next === 'dark' ? 'tối' : 'sáng'}`
  return <button className="theme-switcher theme-toggle" type="button" aria-label={label} title={label} onClick={() => setThemePreference(next)}><WorkspaceIcon name={theme.resolved === 'dark' ? 'moon' : 'sun'} /><span>Giao diện</span></button>
}
