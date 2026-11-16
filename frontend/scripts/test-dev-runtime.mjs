/** Opt-in check against a running local Vite server: SSR must not break client modules. */
import assert from 'node:assert/strict'
import { execFile } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { promisify } from 'node:util'

const origin = new URL(process.argv[2] ?? 'http://127.0.0.1:5173')
assert(origin.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(origin.hostname), 'Local dev server required')
const run = promisify(execFile)

async function moduleDependencies() {
  const entry = await fetch(new URL('/src/app/main.tsx', origin), { signal: AbortSignal.timeout(15000) })
  assert.equal(entry.status, 200, 'Application entry must load')
  const text = await entry.text()
  const dependencies = [...new Set([...text.matchAll(/"(\/node_modules\/[^"\s]+)"/g)].map(m => m[1]))]
  assert(dependencies.length >= 2, 'Expected React runtime dependencies')
  return dependencies
}

async function check(dependencies) {
  for (const path of dependencies) {
    const response = await fetch(new URL(path, origin), { signal: AbortSignal.timeout(15000) })
    assert.equal(response.status, 200, `${path} must load; got ${response.status}`)
    assert.match(response.headers.get('content-type') ?? '', /javascript/, `${path} must be JavaScript`)
  }
}

const before = await moduleDependencies()
await check(before)
for (const script of ['test-report-view.mjs', 'test-repository-view.mjs', 'test-auth.mjs']) {
  const { stdout } = await run(process.execPath, [fileURLToPath(new URL(script, import.meta.url))], { timeout: 90000 })
  process.stdout.write(stdout)
  await check(before)
  await check(await moduleDependencies())
}
console.log('Live Vite React dependencies survived all three SSR suites (not browser acceptance)')
