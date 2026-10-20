@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0local-review-pr.ps1" %*
