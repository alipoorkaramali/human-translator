@echo off
chcp 65001 >nul
title Human Translator
cd /d "%~dp0.."
start "" powershell -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File "%~dp0..\scripts\gui.ps1"
