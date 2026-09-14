@echo off
chcp 65001 >nul
title Human Translator - Setup
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\setup.ps1" %*
echo.
pause
