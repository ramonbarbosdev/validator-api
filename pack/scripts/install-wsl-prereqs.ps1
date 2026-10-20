<#
.SYNOPSIS
  Instala no WSL (Ubuntu) o que o runner Windows precisa para ci-api-validator-cloud-wsl.ps1.
#>
$ErrorActionPreference = "Stop"

if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    throw "WSL nao instalado. No PowerShell (admin): wsl --install"
}

$sh = Join-Path $PSScriptRoot "install-wsl-prereqs.sh"
if (-not (Test-Path $sh)) {
    throw "Falta $sh"
}

$forward = ($sh -replace '\\', '/')
$wslSh = (wsl wslpath -a $forward 2>&1 | Out-String).Trim()
if (-not $wslSh -or $wslSh -match 'wslpath:') {
    throw "wslpath falhou para $sh"
}

Write-Host "Rodando install-wsl-prereqs.sh no WSL..."
wsl bash $wslSh
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Proximo passo: runner self-hosted com VALIDATOR_LOCAL_PATH apontando para este repo." -ForegroundColor Cyan
