<#
.SYNOPSIS
  Executa ci-api-validator.py em modo cloud via WSL (Linux).
  No Windows o cursor-sdk usa bridge local e falha (WinError 10038) mesmo em cloud.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ValidatorRoot,
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    throw "WSL nao encontrado. No Windows use WSL2 ou API_VALIDATOR_EXECUTOR=cloud (ubuntu GitHub)."
}

function ConvertTo-WslPath {
    param([string]$WinPath)
    $resolved = (Resolve-Path $WinPath).Path
    $forward = $resolved -replace '\\', '/'
    $wsl = (wsl wslpath -a $forward 2>&1 | Out-String).Trim()
    if (-not $wsl -or $wsl -match 'wslpath:') {
        throw "wslpath falhou para: $resolved"
    }
    return $wsl
}

function Bash-SingleQuote {
    param([string]$Value)
    if ($null -eq $Value) { return "''" }
    return "'" + ($Value -replace "'", "'\''") + "'"
}

$apiKey = $env:CURSOR_API_KEY
if (-not $apiKey) {
    throw "CURSOR_API_KEY ausente (secret no GitHub ou ambiente)."
}

$repoWsl = ConvertTo-WslPath $RepoRoot
$valWsl = ConvertTo-WslPath $ValidatorRoot
$reqFile = "$valWsl/scripts/requirements-ci.txt"
$ciScript = "$valWsl/scripts/ci-api-validator.py"

$bashLines = @(
    "set -euo pipefail"
    "export CURSOR_API_KEY=$(Bash-SingleQuote $apiKey)"
    "export CURSOR_VALIDATOR_RUNTIME=cloud"
    "export REPO_ROOT=$(Bash-SingleQuote $repoWsl)"
)
foreach ($name in @(
        'GITHUB_REPOSITORY', 'GITHUB_SHA', 'PR_HTML_URL', 'GITHUB_BASE_REF',
        'PR_NUMBER', 'VALIDATOR_REPO', 'VALIDATOR_REF', 'VALIDATOR_PIN_SHA',
        'CURSOR_VALIDATOR_STRICT_REPORT', 'CURSOR_VALIDATOR_MODEL',
        'GITHUB_TOKEN', 'CURSOR_VALIDATOR_PR_COMMENTS', 'CURSOR_VALIDATOR_BOT_LOGINS'
    )) {
    $v = [Environment]::GetEnvironmentVariable($name)
    if ($v) { $bashLines += "export $name=$(Bash-SingleQuote $v)" }
}

$bashLines += @(
    "cd $(Bash-SingleQuote $repoWsl)"
    'VENV="$HOME/.cache/api-validator-ci-venv"'
    'if [[ ! -x "$VENV/bin/python" ]]; then'
    '  if ! python3 -m venv "$VENV" 2>/dev/null; then'
    '    echo "WSL: nao foi possivel criar venv. Rode:" >&2'
    '    echo "  sudo apt update && sudo apt install -y python3-venv python3-pip" >&2'
    '    exit 1'
    '  fi'
    'fi'
    '"$VENV/bin/python" -m pip install -q -U pip'
    '"$VENV/bin/python" -m pip install -q -r ' + (Bash-SingleQuote $reqFile)
    '"$VENV/bin/python" ' + (Bash-SingleQuote $ciScript)
)

$bash = ($bashLines -join "`n") + "`n"

$tempDir = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [System.IO.Path]::GetTempPath() }
$shPath = Join-Path $tempDir "ci-api-validator-cloud-wsl.sh"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($shPath, $bash, $utf8NoBom)
$shWsl = ConvertTo-WslPath $shPath

Write-Host "Windows: executando api-validator (cloud) via WSL..."
Write-Host "Repo: $repoWsl"
wsl bash $(Bash-SingleQuote $shWsl)
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

