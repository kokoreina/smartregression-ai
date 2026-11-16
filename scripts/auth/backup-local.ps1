$ErrorActionPreference = 'Stop'
$taskProject = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if (-not $taskProject.StartsWith('D:\smart-regression-ai\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Project scope required' }
$env:SMARTREGRESSION_WEB_ENV_FILE = Join-Path $taskProject 'var/auth/web.env'
$env:PYTHONPATH = Join-Path $taskProject 'backend/src'
$env:TEMP = Join-Path $taskProject 'var/phase3-8/browser-tmp'
Set-Location -LiteralPath $taskProject
& (Join-Path $taskProject '.venv/Scripts/python.exe') (Join-Path $taskProject 'scripts/auth/backup_local.py')
if ($LASTEXITCODE -ne 0) { throw 'Owned local backup failed' }
