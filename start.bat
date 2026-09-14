@echo off
chcp 65001 >nul
title Human Translator
cd /d "%~dp0"

if not exist "scripts\gui.ps1" (
  echo ERROR: scripts\gui.ps1 not found
  echo Run this from the project root folder.
  pause
  exit /b 1
)

echo Starting Human Translator GUI...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0scripts\gui.ps1"
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
  echo.
  echo GUI exited with code %ERR%
  if exist "data\output\gui-error.log" (
    echo --- gui-error.log ---
    type "data\output\gui-error.log"
  )
  pause
)
