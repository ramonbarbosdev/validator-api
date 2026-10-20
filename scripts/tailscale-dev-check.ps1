<#
  Checagens antes de depender do webhook via VPS + Tailscale.
  Rode com validator-api serve ativo e Tailscale conectado.
#>
$ErrorActionPreference = "Stop"

$ts = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $ts) {
    Write-Host "Tailscale CLI nao encontrado. Instale: https://tailscale.com/download/windows" -ForegroundColor Red
    exit 1
}

$ip = (tailscale ip -4 2>$null | Select-Object -First 1).Trim()
if (-not $ip) {
    Write-Host "Tailscale sem IP (logue na tailnet)." -ForegroundColor Red
    exit 1
}

Write-Host "Tailscale IPv4 deste PC: $ip"
Write-Host "Na VPS, Caddy reverse_proxy deve usar: http://${ip}:8765"
Write-Host "  ou MagicDNS: tailscale status"

try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing -TimeoutSec 3
    if ($r.Content -match "ok") {
        Write-Host "OK  validator-api local em :8765" -ForegroundColor Green
    } else {
        Write-Host "AVISO  :8765 respondeu mas nao parece /health ok" -ForegroundColor Yellow
    }
} catch {
    Write-Host "!!  validator-api nao responde em :8765 — rode .\scripts\start-local.ps1" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Teste da VPS: curl http://${ip}:8765/health"
Write-Host "Webhook GitHub (dev): https://validador-dev.SEUDOMINIO/webhook"
