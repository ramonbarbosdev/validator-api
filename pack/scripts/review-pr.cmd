@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0review-pr.ps1" %*
