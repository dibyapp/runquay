$ErrorActionPreference = 'Stop'
$existingTask = Get-ScheduledTask -TaskName 'AutoWork Local Codex Supervisor' -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName 'AutoWork Local Codex Supervisor' -Confirm:$false
    Write-Output 'AutoWork autostart removed. Your projects, logins, and history are retained.'
}

