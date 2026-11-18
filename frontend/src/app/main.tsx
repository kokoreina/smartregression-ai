import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Application } from './Application'
import './styles.css'
import './account.css'
import './design-tokens.css'
import './workspace.css'
import './themes.css'
import '../features/auth/authPresentation.css'

createRoot(document.getElementById('root')!).render(<StrictMode><Application /></StrictMode>)
