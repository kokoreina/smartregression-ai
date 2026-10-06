import type { components } from '../types/generated'

export async function checkHealth(signal: AbortSignal): Promise<components['schemas']['HealthResponse']> {
  const response = await fetch('/api/health', { signal })
  if (!response.ok) throw new Error(`API trả HTTP ${response.status}`)
  const data: components['schemas']['HealthResponse'] = await response.json()
  if (data.schema_version !== '1.0.0' || data.status !== 'ok' || data.scope !== 'service_only' || data.service !== 'smartregression-api') {
    throw new Error('Health response không đúng contract')
  }
  return data
}
