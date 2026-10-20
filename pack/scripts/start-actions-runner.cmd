@echo off
setlocal EnableExtensions
title GitHub Actions Runner (self-hosted)

rem Ajuste aqui ou defina a variavel de ambiente ACTIONS_RUNNER_HOME
if not defined ACTIONS_RUNNER_HOME set "ACTIONS_RUNNER_HOME=C:\actions-runner"

if not exist "%ACTIONS_RUNNER_HOME%\run.cmd" (
    echo [ERRO] Nao encontrei run.cmd em:
    echo   %ACTIONS_RUNNER_HOME%
    echo.
    echo Edite ACTIONS_RUNNER_HOME neste arquivo ou nas Variaveis de Ambiente do Windows.
    pause
    exit /b 1
)

cd /d "%ACTIONS_RUNNER_HOME%"
echo ========================================
echo  GitHub Actions runner
echo  Pasta: %ACTIONS_RUNNER_HOME%
echo  Mantenha esta janela aberta para jobs (ex.: API Validator na PR).
echo ========================================
echo.

call "%ACTIONS_RUNNER_HOME%\run.cmd"
set "EC=%ERRORLEVEL%"

echo.
echo Runner encerrado (exit %EC%).
pause
exit /b %EC%
