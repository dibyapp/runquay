$ErrorActionPreference = 'Stop'
$workspacePath = $PSScriptRoot
$pythonCommand = (Get-Command python.exe -ErrorAction Stop).Source
$pythonWindowless = Join-Path (Split-Path -Parent $pythonCommand) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonWindowless)) { throw 'pythonw.exe is required for a hidden startup worker.' }
$scriptPath = Join-Path $workspacePath 'supervisor.py'
$taskAction = New-ScheduledTaskAction -Execute $pythonWindowless -Argument ('"' + $scriptPath + '"') -WorkingDirectory $workspacePath
$taskTrigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$taskPrincipal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'AutoWork Local Codex Supervisor' -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -Principal $taskPrincipal -Description 'Local project queue. Subscription-only Codex work with explicit reset approvals.' -Force | Out-Null
Write-Output 'AutoWork autostart installed for this Windows user. It starts after sign-in and restarts on failure.'

