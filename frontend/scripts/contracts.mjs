import { mkdir, readFile, writeFile } from 'node:fs/promises'
import openapiTS, { astToString } from 'openapi-typescript'

const schema = new URL('../../contracts/generated/openapi.json', import.meta.url)
const target = new URL('../src/types/generated.ts', import.meta.url)
const content = '// Generated from backend models. Do not edit.\n' + astToString(await openapiTS(schema, { defaultNonNullable: false }))
if (process.argv.includes('--check')) {
  const current = await readFile(target, 'utf8').catch(() => '')
  if (current !== content) {
    console.error('Types are stale: npm --prefix frontend run contracts:generate')
    process.exitCode = 1
  }
} else {
  await mkdir(new URL('../src/types/', import.meta.url), { recursive: true })
  await writeFile(target, content, 'utf8')
}
