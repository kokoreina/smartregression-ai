param(
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [switch]$RuntimeOnly
)
$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$savedPath = $env:PYTHONPATH
$savedCandidates = $env:SMARTREGRESSION_INVENTORY_CANDIDATES
$savedMapping = $env:SMARTREGRESSION_MAPPING_WORKFLOW
Push-Location $project
try {
    $env:PYTHONPATH = Join-Path $project 'backend\src'
    if (-not $RuntimeOnly) {
        & $PythonExe -m pytest
        if ($LASTEXITCODE -ne 0) { throw 'Default backend tests failed.' }
        & $PythonExe -m ruff check .
        if ($LASTEXITCODE -ne 0) { throw 'Ruff failed.' }
        & $PythonExe -m ruff format --check .
        if ($LASTEXITCODE -ne 0) { throw 'Format check failed.' }
        & $PythonExe scripts/export_contracts.py --check
        if ($LASTEXITCODE -ne 0) { throw 'Contract check failed.' }
    }
    docker build -t smartregression-inventory:candidates-locked -f scripts/inventory/Dockerfile scripts/inventory
    if ($LASTEXITCODE -ne 0) { throw 'Locked candidate image build failed.' }
    $candidateImage = (docker image inspect smartregression-inventory:candidates-locked --format '{{.Id}}').Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Candidate image lookup failed.' }
    $candidateLines = @(& $PythonExe scripts/inventory/verify_candidates.py $candidateImage)
    $candidateExit = $LASTEXITCODE
    $candidateLines | Write-Output
    if ($candidateExit -ne 0) { throw 'Candidate collection failed. Inspect evidence.json.' }
    $candidateResult = $candidateLines[-1] | ConvertFrom-Json
    $env:SMARTREGRESSION_INVENTORY_CANDIDATES = $candidateResult.evidence
    $mappingLines = @(& $PythonExe scripts/mapping/verify_workflow.py --image $candidateImage)
    $mappingExit = $LASTEXITCODE
    $mappingLines | Write-Output
    if ($mappingExit -ne 0) { throw 'Candidate CLI mapping failed. Inspect evidence.json.' }
    $mappingResult = $mappingLines[-1] | ConvertFrom-Json
    $env:SMARTREGRESSION_MAPPING_WORKFLOW = $mappingResult.evidence
    docker build -t smartregression-inventory:owned -f scripts/g1/Dockerfile scripts/g1
    if ($LASTEXITCODE -ne 0) { throw 'Fixture image build failed.' }
    $fixtureImage = (docker image inspect smartregression-inventory:owned --format '{{.Id}}').Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Fixture image lookup failed.' }
    $fixtureOutput = Join-Path $project ('var\inventory-verification-' + [guid]::NewGuid().ToString('N'))
    & $PythonExe scripts/inventory/run_checks.py --image $fixtureImage --output $fixtureOutput
    if ($LASTEXITCODE -ne 0) { throw 'Fixture collection failed. Inspect evidence.json.' }
    & $PythonExe scripts/storage/run_checks.py
    if ($LASTEXITCODE -ne 0) { throw 'Inventory PostgreSQL checks failed. Inspect evidence.json.' }
} finally {
    $env:PYTHONPATH = $savedPath
    $env:SMARTREGRESSION_INVENTORY_CANDIDATES = $savedCandidates
    $env:SMARTREGRESSION_MAPPING_WORKFLOW = $savedMapping
    Pop-Location
}
