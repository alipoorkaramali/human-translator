@echo off
chcp 65001 >nul
title Human Translator
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\restore-gui.ps1"
start "" powershell -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File "%~dp0scripts\gui.ps1"
