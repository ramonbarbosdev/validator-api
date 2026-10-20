@echo off
setlocal
set CURSOR_VALIDATOR_RUNTIME=cloud
call "%~dp0run-api-validator.cmd" %*
