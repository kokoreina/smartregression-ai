param([string]$PythonExe = 'python')

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskOldLocation = Get-Location
$taskOldPythonPath = $env:PYTHONPATH
try {
    Set-Location -LiteralPath $taskRoot
    $taskDockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
    if ($null -eq $taskDockerCommand) {
        throw 'Docker is not on PATH. Open Docker Desktop, then a new PowerShell window.'
    }
    & $taskDockerCommand.Source version --format '{{.Server.Version}}'
    if ($LASTEXITCODE -ne 0) { throw 'Docker Linux engine is unavailable to this terminal.' }
    & $PythonExe -c 'import sys, pytest, pydantic; assert sys.version_info[:2] == (3,14)'
    if ($LASTEXITCODE -ne 0) { throw 'Use the SmartRegression Python 3.14 environment with locked dependencies.' }

    $taskBase = 'python@sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8'
    & $taskDockerCommand.Source build --build-arg "PYTHON_IMAGE=$taskBase" --tag smartregression-g1:spike --file scripts/g1-image/Dockerfile scripts/g1-image
    if ($LASTEXITCODE -ne 0) { throw 'G1 image build failed. No fixture test was executed.' }
    $taskImageId = & $taskDockerCommand.Source image inspect --format '{{.Id}}' smartregression-g1:spike
    if ($LASTEXITCODE -ne 0 -or $taskImageId -notmatch '^sha256:[0-9a-f]{64}$') {
        throw 'Immutable local image identity could not be verified.'
    }
    New-Item -ItemType Directory -Path var -Force | Out-Null
    [ordered]@{
        base_image = $taskBase
        image_id = $taskImageId
        observed_at = [DateTimeOffset]::UtcNow.ToString('o')
        data_kind = 'owned_fixture_spike'
    } | ConvertTo-Json | Set-Content -LiteralPath var/g1-image.json -Encoding utf8
    $env:PYTHONPATH = Join-Path $taskRoot 'backend\src'
    & $PythonExe scripts/spike_g1.py --image $taskImageId
    if ($LASTEXITCODE -ne 0) { throw 'G1 did not complete. Inspect the evidence.json path printed above.' }
    Write-Output 'G1 mechanics demonstrated on the owned fixture. This is not a benchmark or production-isolation claim.'
} finally {
    $env:PYTHONPATH = $taskOldPythonPath
    Set-Location -LiteralPath $taskOldLocation.Path
}
