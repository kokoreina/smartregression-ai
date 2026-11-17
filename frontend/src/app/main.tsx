import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Application } from './Application'
import './styles.css'
import './account.css'

createRoot(document.getElementById('root')!).render(<StrictMode><Application /></StrictMode>)
