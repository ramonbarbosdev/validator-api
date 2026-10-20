@echo off
REM Validacao 100%% local no Windows: install + prompt; IA no Cursor (/api-validator). Sem Cloud Agent.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0local-review-pr.ps1" %*
if errorlevel 1 exit /b 1
echo.
echo === Validacao LOCAL (Cursor IDE) ===
echo 1. Abra o arquivo de prompt indicado acima
echo 2. Chat -^> /api-validator -^> cole o bloco text
echo 3. Copie o relatorio para a PR no GitHub (se quiser)
echo.
echo Nao usa CURSOR_API_KEY nem cota Cloud Agent.
exit /b 0
