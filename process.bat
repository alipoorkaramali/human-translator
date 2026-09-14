@echo off
chcp 65001 >nul
title Text Processor - One Shot
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run-once.ps1" %*
echo.
pause
