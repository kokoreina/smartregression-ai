param([Parameter(Mandatory=$true)][string]$PythonExe, [switch]$RuntimeOnly)
$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$savedPath = $env:PYTHONPATH
Push-Location $project
try {
    $env:PYTHONPATH = Join-Path $project 'backend\src'
    if (-not $RuntimeOnly) {
        & $PythonExe -m pytest
        if ($LASTEXITCODE -ne 0) { throw 'Default tests failed.' }
        & $PythonExe -m ruff check .
        if ($LASTEXITCODE -ne 0) { throw 'Ruff failed.' }
        & $PythonExe -m ruff format --check .
        if ($LASTEXITCODE -ne 0) { throw 'Format check failed.' }
        & $PythonExe scripts/export_contracts.py --check
        if ($LASTEXITCODE -ne 0) { throw 'Contract check failed.' }
    }
    docker build -t smartregression-inventory:candidates-locked -f scripts/inventory/Dockerfile scripts/inventory
    if ($LASTEXITCODE -ne 0) { throw 'Locked image build failed.' }
    $image = (docker image inspect smartregression-inventory:candidates-locked --format '{{.Id}}').Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Image lookup failed.' }
    $lines = @(& $PythonExe scripts/inventory/verify_candidates.py $image)
    $resultCode = $LASTEXITCODE
    $lines | Write-Output
    if ($resultCode -ne 0) { throw 'Candidate collection failed. Inspect evidence.json.' }
    $result = $lines[-1] | ConvertFrom-Json
    & $PythonExe scripts/mapping/verify_candidates.py --collection-evidence $result.evidence
    if ($LASTEXITCODE -ne 0) { throw 'Mapping verification failed. Inspect evidence.json.' }
} finally {
    $env:PYTHONPATH = $savedPath
    Pop-Location
}
