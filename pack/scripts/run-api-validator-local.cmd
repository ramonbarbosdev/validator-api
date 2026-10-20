@echo off
setlocal
set CURSOR_VALIDATOR_RUNTIME=local
set CURSOR_VALIDATOR_FORCE_LOCAL=1
call "%~dp0run-api-validator.cmd" %*
