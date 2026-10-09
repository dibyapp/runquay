param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
function Refresh-SetupPath {
    $env:PATH = [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH','User') + ';' + $env:PATH
}
function Find-SetupPython {
    foreach($candidate in @('py','python','python3')) {
        $pythonCommand = Get-Command $candidate -ErrorAction SilentlyContinue
        if($pythonCommand) {
            $arguments = @('-c','import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 2)')
            if($candidate -eq 'py'){$arguments = @('-3') + $arguments}
            & $pythonCommand.Source @arguments 2>$null
            if($LASTEXITCODE -eq 0){return @{Path=$pythonCommand.Source; Prefix=$(if($candidate -eq 'py'){@('-3')}else{@()})}}
        }
    }
    return $null
}
Refresh-SetupPath
$setupPython = Find-SetupPython
$setupGit = Get-Command git -ErrorAction SilentlyContinue
Write-Output 'Runquay setup: Windows detected.'
if($CheckOnly){Write-Output "Python 3.11+: $([bool]$setupPython); Git: $([bool]$setupGit)"; exit 0}
if(!$setupPython -or !$setupGit){
    $setupWinget = Get-Command winget -ErrorAction SilentlyContinue
    if(!$setupWinget){throw 'Install App Installer (WinGet) from Microsoft, or Python 3.11+ and Git from their official websites. See docs/SETUP.md.'}
    Write-Output 'Installing only missing Python/Git through WinGet. Finish any OS permission or vendor agreement prompts here.'
    if(!$setupPython){& $setupWinget.Source install --id Python.Python.3.13 --exact --source winget --no-upgrade; if($LASTEXITCODE -ne 0){throw 'Python installation did not finish.'}}
    if(!$setupGit){& $setupWinget.Source install --id Git.Git --exact --source winget --no-upgrade; if($LASTEXITCODE -ne 0){throw 'Git installation did not finish.'}}
    Refresh-SetupPath
    $setupPython = Find-SetupPython
    if(!$setupPython -or !(Get-Command git -ErrorAction SilentlyContinue)){throw 'Reopen setup.cmd to pick up the newly installed tools.'}
}
Write-Output 'Essentials are ready. Opening the guided dashboard. Keep this window open while Runquay runs.'
$setupArguments = @($setupPython.Prefix) + @('runquay.py','start')
& $setupPython.Path @setupArguments
exit $LASTEXITCODE
