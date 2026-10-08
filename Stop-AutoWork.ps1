$ErrorActionPreference = 'Stop'
$registeredTask = Get-ScheduledTask -TaskName 'AutoWork Local Codex Supervisor' -ErrorAction SilentlyContinue
if ($registeredTask -and $registeredTask.State -eq 'Running') {
    Stop-ScheduledTask -TaskName 'AutoWork Local Codex Supervisor'
}
$pidFile = Join-Path $PSScriptRoot 'data\supervisor.pid'
if (-not (Test-Path -LiteralPath $pidFile)) {
    $pidFile = Join-Path $env:LOCALAPPDATA 'AutoWork\supervisor.pid'
}
if (Test-Path -LiteralPath $pidFile) {
    $workerPid = [int](Get-Content -LiteralPath $pidFile)
    $workerProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $workerPid"
    $expectedScript = Join-Path $PSScriptRoot 'supervisor.py'
    if ($workerProcess -and $workerProcess.CommandLine.Contains($expectedScript) -and $workerProcess.Name -match '^pythonw?\.exe$') {
        Stop-Process -Id $workerPid
        Write-Output 'AutoWork stopped. Active Codex children are stopped by Windows containment.'
    } else { Write-Output 'No matching AutoWork process found; no process was stopped.' }
}
