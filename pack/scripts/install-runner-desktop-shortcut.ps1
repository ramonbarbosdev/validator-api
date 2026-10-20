<#
.SYNOPSIS
  Cria atalho na Area de Trabalho para ligar o GitHub Actions runner (run.cmd).
#>
param(
    [string]$RunnerHome = "",
    [string]$ShortcutName = "GitHub Actions Runner.lnk"
)

$ErrorActionPreference = "Stop"

if (-not $RunnerHome) {
    if ($env:ACTIONS_RUNNER_HOME) { $RunnerHome = $env:ACTIONS_RUNNER_HOME }
    else { $RunnerHome = "C:\actions-runner" }
}

$RunnerHome = (Resolve-Path $RunnerHome -ErrorAction SilentlyContinue).Path
if (-not $RunnerHome -or -not (Test-Path (Join-Path $RunnerHome "run.cmd"))) {
    throw "Runner invalido (falta run.cmd): $RunnerHome. Passe -RunnerHome ou registre o runner em actions-runner."
}

$launcher = Join-Path $PSScriptRoot "start-actions-runner.cmd"
if (-not (Test-Path $launcher)) {
    throw "Falta $launcher"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop $ShortcutName

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)
$sc.TargetPath = $launcher
$sc.WorkingDirectory = $RunnerHome
$sc.WindowStyle = 1
$sc.Description = "Self-hosted runner para GitHub Actions (esimples-api)"
$sc.Save()

[System.Environment]::SetEnvironmentVariable(
    "ACTIONS_RUNNER_HOME",
    $RunnerHome,
    [System.EnvironmentVariableTarget]::User
)

Write-Host "Atalho criado: $shortcutPath"
Write-Host "ACTIONS_RUNNER_HOME (usuario) = $RunnerHome"
Write-Host "Duplo clique no atalho para ligar o runner."
