param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [ValidateSet("", "java-spring-esimples")]
    [string]$Stack = ""
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Target = (Resolve-Path $Target).Path

function Copy-Merge($From, $To) {
    if (-not (Test-Path $From)) { return }
    New-Item -ItemType Directory -Force -Path $To | Out-Null
    Copy-Item -Path (Join-Path $From "*") -Destination $To -Recurse -Force
}

Write-Host "Instalando cursor-api-validator-java em: $Target"

Copy-Merge (Join-Path $PackageRoot ".cursor") (Join-Path $Target ".cursor")
Copy-Merge (Join-Path $PackageRoot "docs\validador") (Join-Path $Target "docs\validador")
Copy-Merge (Join-Path $PackageRoot "docs\padrao") (Join-Path $Target "docs\padrao")

$specTemplate = Join-Path $PackageRoot "docs\SPEC.template.md"
if (Test-Path $specTemplate) {
    Copy-Item $specTemplate (Join-Path $Target "docs\SPEC.template.md") -Force
}

if ($Stack -eq "java-spring-esimples") {
    $stackRoot = Join-Path $PackageRoot "stacks\java-spring-esimples"
    Copy-Merge (Join-Path $stackRoot "docs\padrao") (Join-Path $Target "docs\padrao")
    $overlay = Join-Path $stackRoot "docs\validador\revisao.overlay.md"
    if (Test-Path $overlay) {
        Copy-Item $overlay (Join-Path $Target "docs\validador\revisao.overlay.md") -Force
    }
    Write-Host "Stack java-spring-esimples aplicado."
}

Write-Host "Concluido. Revise templates/AGENTS.snippet.md e commit .cursor + docs."
