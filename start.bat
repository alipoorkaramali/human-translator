@echo off
chcp 65001 >nul
title Human Translator
cd /d "%~dp0"

if not exist "scripts\gui.ps1" (
  echo ERROR: scripts\gui.ps1 not found.
  echo Make sure you opened start.bat from the project root.
  pause
  exit /b 1
)

REM -STA is required for WinForms. Without it the window often closes immediately.
REM Errors are also written to data\output\gui-error.log
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0scripts\gui.ps1"
if errorlevel 1 (
  echo.
  echo GUI exited with an error. See data\output\gui-error.log
  if exist "data\output\gui-error.log" type "data\output\gui-error.log"
  pause
)
