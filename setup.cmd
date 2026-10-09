@echo off
setlocal
cd /d "%~dp0"
echo Runquay setup: Windows detected.
call :detect_python
set "setupGit="
where git >nul 2>nul
if not errorlevel 1 set "setupGit=ready"
if "%~1"=="--check" goto report
if not defined setupPython goto install
if not defined setupGit goto install
goto launch

:install
where winget >nul 2>nul
if errorlevel 1 (
  echo Install App Installer - WinGet - from Microsoft, or Python 3.11+ and Git from their official websites.
  echo See docs\SETUP.md, then reopen this file.
  goto failed
)
echo Installing only missing Python and Git. Finish any OS permission or vendor agreement prompts here.
if defined setupPython goto git_install
winget install --id Python.Python.3.13 --exact --source winget --no-upgrade
if errorlevel 1 goto failed
:git_install
if defined setupGit goto refresh
winget install --id Git.Git --exact --source winget --no-upgrade
if errorlevel 1 goto failed
:refresh
rem These known vendor locations apply only to this launcher, not the global PATH.
set "PATH=%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Launcher;%ProgramFiles%\Python313;%ProgramFiles%\Git\cmd;%PATH%"
call :detect_python
if not defined setupPython goto reopen
where git >nul 2>nul
if errorlevel 1 goto reopen
:launch
echo Essentials are ready. Opening the guided dashboard. Keep this window open while Runquay runs.
%setupPython% %setupPythonPrefix% runquay.py start
if errorlevel 1 goto failed
exit /b 0
:reopen
echo Reopen setup.cmd to pick up the newly installed tools.
:failed
echo Setup did not finish. Read the message above and docs\SETUP.md.
pause
exit /b 2
:report
if defined setupPython (echo Python 3.11+: ready) else (echo Python 3.11+: missing)
if defined setupGit (echo Git: ready) else (echo Git: missing)
exit /b 0

:detect_python
set "setupPython="
set "setupPythonPrefix="
where py >nul 2>nul
if errorlevel 1 goto detect_plain
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 2)" >nul 2>nul
if errorlevel 1 goto detect_plain
set "setupPython=py"
set "setupPythonPrefix=-3"
exit /b 0
:detect_plain
where python >nul 2>nul
if errorlevel 1 exit /b 0
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 2)" >nul 2>nul
if errorlevel 1 exit /b 0
set "setupPython=python"
exit /b 0
