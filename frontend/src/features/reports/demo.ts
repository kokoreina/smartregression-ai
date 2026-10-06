import type { components } from '../../types/generated'

export type AnalysisReport = components['schemas']['AnalysisReport']

export async function loadDemo(): Promise<AnalysisReport> {
  // This bundled JSON is validated by the backend exporter and CI, not user input.
  const { default: fixture } = await import('../../../../examples/reports/demo.json')
  if (fixture.data_kind !== 'demo') throw new Error('Fixture phải có nhãn DEMO')
  return fixture as AnalysisReport
}
