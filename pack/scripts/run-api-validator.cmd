@echo off
REM Prepara install + gera relatorio (CURSOR_API_KEY no .env ou no ambiente).
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0local-review-pr.ps1" %*
if errorlevel 1 exit /b 1

if not exist pom.xml (
  echo Execute na raiz do esimples-api.
  exit /b 1
)

set VALIDATOR_ROOT=%~dp0..
if defined CURSOR_API_VALIDATOR_ROOT set VALIDATOR_ROOT=%CURSOR_API_VALIDATOR_ROOT%
set REPO_ROOT=%CD%

if not defined CURSOR_VALIDATOR_RUNTIME set CURSOR_VALIDATOR_RUNTIME=cloud

echo Instalando dependencias (cursor-sdk) se necessario...
py -3 -m pip install -q -r "%VALIDATOR_ROOT%\scripts\requirements-ci.txt"
if errorlevel 1 python -m pip install -q -r "%VALIDATOR_ROOT%\scripts\requirements-ci.txt"

echo.
echo Executando api-validator (runtime=%CURSOR_VALIDATOR_RUNTIME%)...
if /I "%CURSOR_VALIDATOR_RUNTIME%"=="cloud" (
  echo Cloud: branch no GitHub ^(git push^). Chave: CURSOR_API_KEY no .env
) else (
  echo Local: SDK no workspace. Windows: prefira run-api-validator-cloud.cmd
)
echo.
py -3 "%VALIDATOR_ROOT%\scripts\ci-api-validator.py"
if errorlevel 1 python "%VALIDATOR_ROOT%\scripts\ci-api-validator.py"
if errorlevel 1 exit /b 1

if exist "%REPO_ROOT%\api-validator-report.md" (
  echo.
  echo === RELATORIO ===
  type "%REPO_ROOT%\api-validator-report.md"
  echo.
  echo Salvo em: %REPO_ROOT%\api-validator-report.md
)
