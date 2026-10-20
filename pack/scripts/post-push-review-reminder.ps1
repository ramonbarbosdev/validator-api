<#
  Opcional: lembrete local após git push (NÃO substitui o runner).
  Instale como hook: copie para .git/hooks/post-push ou chame manualmente.

  Requer: gh auth login (para detectar PR da branch atual).
#>
param([string]$AppDir = "")

$ErrorActionPreference = "Stop"
if (-not $AppDir) {
    $AppDir = (Get-Location).Path
    if (-not (Test-Path (Join-Path $AppDir "pom.xml"))) {
        Write-Host "Execute na raiz do esimples-api."
        exit 1
    }
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "Sem gh: após o push, rode local-review-pr.ps1 manualmente."
    exit 0
}

Push-Location $AppDir
$branch = git branch --show-current
$prJson = gh pr list --head $branch --state open --json number -q '.[0].number' 2>$null
Pop-Location

if ($prJson) {
    Write-Host "PR #$prJson aberta — runner self-hosted deve validar no GitHub Actions."
    Write-Host "Local: ..\cursor-api-validator-java\scripts\local-review-pr.ps1 -Pr $prJson"
} else {
    Write-Host "Nenhuma PR aberta para a branch $branch."
}
