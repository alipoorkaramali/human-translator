@echo off
chcp 65001 >nul
title Text Processor - Watch Mode
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\watch.ps1"
echo.
pause
