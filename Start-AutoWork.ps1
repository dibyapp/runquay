param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$workspacePath = $PSScriptRoot
$pythonCommand = (Get-Command python.exe -ErrorAction Stop).Source
$pythonWindowless = Join-Path (Split-Path -Parent $pythonCommand) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonWindowless)) { $pythonWindowless = $pythonCommand }
$isOnline = $false
try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/' -TimeoutSec 2; $isOnline = $response.StatusCode -eq 200 -and $response.Content.Contains('AutoWork') } catch {}
if (-not $isOnline) {
    $scriptPath = Join-Path $workspacePath 'supervisor.py'
    Start-Process -FilePath $pythonWindowless -ArgumentList @('"' + $scriptPath + '"') -WorkingDirectory $workspacePath -WindowStyle Hidden
}
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765/' }

