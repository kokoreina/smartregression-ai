param([Parameter(Mandatory=$true)][string]$PythonExe, [switch]$DatabaseOnly)
$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$savedPath = $env:PYTHONPATH
Push-Location $project
try {
    $env:PYTHONPATH = Join-Path $project 'backend\src'
    if (-not $DatabaseOnly) {
        & $PythonExe -m pytest
        if ($LASTEXITCODE -ne 0) { throw 'Default tests failed.' }
        & $PythonExe -m ruff check .
        if ($LASTEXITCODE -ne 0) { throw 'Ruff failed.' }
        & $PythonExe -m ruff format --check .
        if ($LASTEXITCODE -ne 0) { throw 'Format check failed.' }
        & $PythonExe scripts/export_contracts.py --check
        if ($LASTEXITCODE -ne 0) { throw 'Contract check failed.' }
    }
    & $PythonExe scripts/storage/run_checks.py
    if ($LASTEXITCODE -ne 0) { throw 'Index/PostgreSQL verification failed. Inspect evidence.json.' }
} finally {
    $env:PYTHONPATH = $savedPath
    Pop-Location
}
