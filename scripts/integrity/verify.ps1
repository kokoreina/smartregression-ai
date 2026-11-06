param([Parameter(Mandatory=$true)][string]$PythonExe, [switch]$RuntimeOnly)
$ErrorActionPreference = 'Stop'
$project = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$savedPath = $env:PYTHONPATH
Push-Location $project
try {
    $env:PYTHONPATH = Join-Path $project 'backend\src'
    $arguments = @('scripts/integrity/verify.py')
    if ($RuntimeOnly) { $arguments += '--runtime-only' }
    & $PythonExe @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Task 2.19 verification failed. Inspect evidence.json.' }
} finally {
    $env:PYTHONPATH = $savedPath
    Pop-Location
}
