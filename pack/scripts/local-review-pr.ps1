<#
.SYNOPSIS
  Maquina local: prepara review da PR (ou da branch atual) no esimples-api.
#>
param(
    [int]$Pr = 0,
    [string]$AppDir = "",
    [string]$Base = "develop",
    [string]$ValidatorRoot = ""
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git @Args 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { throw "git $($Args -join ' ') falhou (exit $code)" }
}

function Invoke-GitOut {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & git @Args 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { return $null }
    return $out
}

if (-not $AppDir) {
    $here = (Get-Location).Path
    if (Test-Path (Join-Path $here "pom.xml")) { $AppDir = $here }
    else { throw "Execute na raiz do esimples-api ou passe -AppDir." }
}
$AppDir = (Resolve-Path $AppDir).Path

if (-not $ValidatorRoot) {
    $sibling = Join-Path (Split-Path $AppDir -Parent) "cursor-api-validator-java"
    if (Test-Path $sibling) { $ValidatorRoot = $sibling }
    elseif ($env:CURSOR_API_VALIDATOR_ROOT) { $ValidatorRoot = $env:CURSOR_API_VALIDATOR_ROOT }
    else { throw "Nao encontrei cursor-api-validator-java. Passe -ValidatorRoot ou CURSOR_API_VALIDATOR_ROOT." }
}
$ValidatorRoot = (Resolve-Path $ValidatorRoot).Path

$reviewScript = Join-Path $ValidatorRoot "scripts\review-pr.ps1"
if (-not (Test-Path $reviewScript)) { throw "Falta $reviewScript" }

if ($Pr -gt 0) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $reviewScript -AppDir $AppDir -Pr $Pr -Base $Base -Stack java-spring-esimples
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $prompt = Join-Path $AppDir ".api-validator-review\pr-$Pr-prompt.md"
} else {
    Push-Location $AppDir
    Invoke-Git fetch origin $Base
    $baseRef = "origin/$Base"
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & git rev-parse --verify $baseRef 2>&1 | Out-Null
    $ErrorActionPreference = $prev
    if ($LASTEXITCODE -ne 0) { $baseRef = $Base }

    $install = Join-Path $ValidatorRoot "install\install.ps1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $install -Target $AppDir -Stack java-spring-esimples
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }

    $branch = (Invoke-GitOut branch --show-current).ToString().Trim()
    $headSha = (Invoke-GitOut rev-parse HEAD).ToString().Trim()
    $diffStat = Invoke-GitOut diff --stat "$baseRef...HEAD"
    if (-not $diffStat) { $diffStat = Invoke-GitOut diff --stat $baseRef HEAD }

    $outDir = Join-Path $AppDir ".api-validator-review"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $patch = Invoke-GitOut diff "$baseRef...HEAD"
    if (-not $patch) { $patch = Invoke-GitOut diff $baseRef HEAD }
    $patch | Out-File -Encoding utf8 (Join-Path $outDir "branch-diff.patch")

    if (Test-Path (Join-Path $AppDir "docs\SPEC.md")) {
        $specLine = "SPEC: docs/SPEC.md - escopo ampliado se houver Contrato HTTP; validador inteligente."
    } else {
        $specLine = "Sem docs/SPEC.md: gate enxuto (so diff)."
    }

    $fence = '```'
    $promptLines = @(
        "# Prompt - api-validator (branch local)",
        "",
        "**Branch:** $branch | **Base:** $baseRef | **HEAD:** $headSha",
        "",
        ($fence + "text"),
        "/api-validator branch $branch - diff vs $baseRef.",
        $specLine,
        "Seguir .cursor/agents/api-validator.md e .cursor/skills/revisao-api/SKILL.md - somente relatorio.",
        $fence,
        "",
        "## git diff --stat",
        $fence,
        ($diffStat | Out-String).Trim(),
        $fence,
        "",
        "Diff: .api-validator-review/branch-diff.patch"
    )
    $prompt = Join-Path $outDir "branch-prompt.md"
    ($promptLines -join [Environment]::NewLine) | Out-File -Encoding utf8 $prompt
    Pop-Location
}

Write-Host ""
Write-Host "=== Preparacao concluida (ainda NAO e o relatorio da IA) ===" -ForegroundColor Cyan
Write-Host "Prompt: $prompt"
Write-Host ""
Write-Host "Validacao LOCAL (recomendado no Windows):" -ForegroundColor Yellow
Write-Host "  Chat -> /api-validator -> cole o bloco text do prompt acima (sem Cloud Agent)"
Write-Host "Opcional (cloud, usa API): run-api-validator-cloud.cmd apos git push"
Write-Host ""
if ($Pr -gt 0 -and -not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Dica: instale GitHub CLI (gh) para checkout automatico da PR." -ForegroundColor DarkYellow
}
