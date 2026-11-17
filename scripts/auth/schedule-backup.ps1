$ErrorActionPreference = 'Stop'
$taskProject = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if (-not $taskProject.StartsWith('D:\smart-regression-ai\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Project scope required' }
$taskName = 'SmartRegression-MainPreview-LocalBackup'
$taskScript = Join-Path $taskProject 'scripts/auth/backup-local.ps1'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and ($existing.Actions.Arguments -notcontains ('-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $taskScript + '"'))) { throw 'Existing task ownership mismatch' }
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $taskScript + '"') -WorkingDirectory $taskProject
$trigger = New-ScheduledTaskTrigger -Daily -At '02:00'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description ('Owned local backups only: ' + $taskProject) -Force | Out-Null
Export-ScheduledTask -TaskName $taskName | Set-Content -LiteralPath (Join-Path $taskProject 'var/phase3-8/backup-task.xml') -Encoding utf8
Write-Output 'Daily local backup task registered; requires this user to be logged in and Docker available.'
