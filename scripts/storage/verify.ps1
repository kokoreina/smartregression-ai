param([switch]$DatabaseOnly)
$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$pythonExe = Join-Path $project '.venv\Scripts\python.exe'
$savedPath = $env:PYTHONPATH
Push-Location $project
try {
    $env:PYTHONPATH = Join-Path $project 'backend\src'
    if (-not $DatabaseOnly) {
        & $pythonExe -m pytest
        if ($LASTEXITCODE -ne 0) { throw 'Default backend tests failed.' }
        & $pythonExe -m ruff check .
        if ($LASTEXITCODE -ne 0) { throw 'Ruff failed.' }
        & $pythonExe -m ruff format --check .
        if ($LASTEXITCODE -ne 0) { throw 'Format check failed.' }
        & $pythonExe scripts/export_contracts.py --check
        if ($LASTEXITCODE -ne 0) { throw 'Contract check failed.' }
    }
    & $pythonExe scripts/storage/run_checks.py
    if ($LASTEXITCODE -ne 0) { throw 'Dedicated PostgreSQL verification failed. Inspect evidence.json.' }
} finally {
    $env:PYTHONPATH = $savedPath
    Pop-Location
}
