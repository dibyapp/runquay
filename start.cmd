@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 runquay.py start %*
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Install Python 3.11 or newer from https://www.python.org/downloads/windows/
    echo Select the installer's option to add Python to PATH, then reopen this file.
    echo Read docs\BEGINNERS.md for the step-by-step guide.
    pause
    exit /b 2
  )
  python runquay.py start %*
)
if errorlevel 1 (
  echo.
  echo Runquay could not start. Read the message above and docs\BEGINNERS.md.
  pause
)
