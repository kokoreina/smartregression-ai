param([string]$PythonExe = 'python')

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskOldLocation = Get-Location
$taskOldPythonPath = $env:PYTHONPATH
$taskChecks = @()
try {
    Set-Location -LiteralPath $taskRoot
    $env:PYTHONPATH = Join-Path $taskRoot 'backend\src'
    foreach ($taskCheck in @(
        @{ Name = 'pytest-default'; Args = @('-m', 'pytest', '-q', '-p', 'no:cacheprovider') },
        @{ Name = 'ruff-check'; Args = @('-m', 'ruff', 'check', '.') },
        @{ Name = 'ruff-format'; Args = @('-m', 'ruff', 'format', '--check', '.') },
        @{ Name = 'contract-check'; Args = @('scripts/export_contracts.py', '--check') }
    )) {
        Write-Output ("Running " + $taskCheck.Name)
        $taskArguments = $taskCheck.Args
        & $PythonExe @taskArguments
        $taskExit = $LASTEXITCODE
        $taskChecks += [ordered]@{ name = $taskCheck.Name; exit_code = $taskExit }
    }
    if (@($taskChecks | Where-Object { $_.exit_code -ne 0 }).Count -ne 0) {
        throw 'One or more source checks failed; inspect the results above.'
    }
    & (Join-Path $PSScriptRoot 'run_g1.ps1') -PythonExe $PythonExe
    $taskChecks += [ordered]@{ name = 'docker-g1'; exit_code = 0 }
} finally {
    New-Item -ItemType Directory -Path (Join-Path $taskRoot 'var') -Force | Out-Null
    [ordered]@{
        observed_at = [DateTimeOffset]::UtcNow.ToString('o')
        checks = $taskChecks
        context = 'operator-terminal-no-diagnostic-fixture'
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskRoot 'var/sprint1-verification.json') -Encoding utf8
    $env:PYTHONPATH = $taskOldPythonPath
    Set-Location -LiteralPath $taskOldLocation.Path
}
