@echo off
chcp 65001 >nul
title Human Translator - Auto Watch
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\watch.ps1" %*
echo.
pause
