@echo off
chcp 65001 >nul
title Human Translator - Process Once
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\run-once.ps1" %*
echo.
pause
