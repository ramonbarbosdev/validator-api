<#
  Sobe validator-api em dev local (Windows).
  Uso: na raiz do repo validator-api:
    .\scripts\start-local.ps1
    .\scripts\start-local.ps1 -Doctor   # so checagens, nao sobe servidor
#>
param(
    [switch]$Doctor
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$envFile = Join-Path $repoRoot ".env"
if (-not (Test-Path $envFile)) {
    $legacy = Join-Path (Split-Path $repoRoot -Parent) "cursor-api-validator-java\scripts\.env.pr-review"
    if (Test-Path $legacy) {
        Write-Host "Copiando $legacy -> .env (ajuste REPO_ROOT e comente CURSOR_API_VALIDATOR_ROOT)" -ForegroundColor Yellow
        Copy-Item $legacy $envFile
    } else {
        Write-Host "Crie .env: copy env.example .env" -ForegroundColor Red
        exit 1
    }
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
    $n, $v = $_ -split '=', 2
    [Environment]::SetEnvironmentVariable($n.Trim(), $v.Trim(), "Process")
}

$venvActivate = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}

if (-not $env:REPO_ROOT) {
    $sibling = Join-Path (Split-Path $repoRoot -Parent) "esimples-api"
    if (Test-Path (Join-Path $sibling "pom.xml")) {
        $env:REPO_ROOT = $sibling
    }
}

$cli = Get-Command validator-api -ErrorAction SilentlyContinue
if (-not $cli) {
    $py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
    Write-Host "validator-api nao no PATH; rode: pip install -e ." -ForegroundColor Yellow
    if ($Doctor) { & $py -3 -m validator_api.cli doctor; exit $LASTEXITCODE }
    & $py -3 -m validator_api.cli serve
    exit $LASTEXITCODE
}

if ($Doctor) {
    validator-api doctor
    exit $LASTEXITCODE
}

Write-Host "REPO_ROOT=$env:REPO_ROOT"
Write-Host "Health: http://127.0.0.1:8765/health"
Write-Host "Status: http://127.0.0.1:8765/api/v1/status"
Write-Host "Webhook (ngrok): https://SEU-TUNEL.ngrok-free.app/webhook"
Write-Host "Sem ngrok: validator-api run --pr N"
validator-api serve
