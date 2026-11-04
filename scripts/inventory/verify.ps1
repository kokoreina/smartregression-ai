param([Parameter(Mandatory=$true)][string]$PythonExe)
$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$savedPath = $env:PYTHONPATH
Push-Location $project
try {
    $env:PYTHONPATH = Join-Path $project 'backend\src'
    & $PythonExe -m pytest
    if ($LASTEXITCODE -ne 0) { throw 'Default backend tests failed.' }
    & $PythonExe -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw 'Ruff failed.' }
    & $PythonExe -m ruff format --check .
    if ($LASTEXITCODE -ne 0) { throw 'Format check failed.' }
    & $PythonExe scripts/export_contracts.py --check
    if ($LASTEXITCODE -ne 0) { throw 'Contract check failed.' }
    docker build -t smartregression-inventory:owned -f scripts/g1/Dockerfile scripts/g1
    if ($LASTEXITCODE -ne 0) { throw 'Fixture image build failed.' }
    $inventoryImage = (docker image inspect smartregression-inventory:owned --format '{{.Id}}').Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Image lookup failed.' }
    $output = Join-Path $project ('var\inventory-verification-' + [guid]::NewGuid().ToString('N'))
    & $PythonExe scripts/inventory/run_checks.py --image $inventoryImage --output $output
    if ($LASTEXITCODE -ne 0) { throw 'Isolated inventory checks failed. Inspect evidence.json.' }
} finally {
    $env:PYTHONPATH = $savedPath
    Pop-Location
}
