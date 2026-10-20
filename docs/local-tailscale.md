# Webhook local via Tailscale + VPS

Fluxo completo (commit na PR → GitHub → sua máquina) **sem ngrok**:

```text
GitHub
  → https://validador-dev.seudominio.com/webhook   (TLS na VPS, Caddy)
  → http://SEU-PC:8765                             (IP/host Tailscale do Windows)
  → validator-api serve (REPO_ROOT = esimples-api local)
```

Produção futura na mesma VPS usa outro host (ex. `validador.seudominio.com` → container Docker `:8765`). **Não misture** os dois no mesmo webhook sem querer.

## 1. Tailscale (uma vez)

1. Crie conta em [tailscale.com](https://tailscale.com) (plano free basta para poucos dispositivos).
2. **Windows (dev):** instale [Tailscale for Windows](https://tailscale.com/download/windows), entre na mesma tailnet.
3. **VPS (Linux):** na VPS:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
4. No [admin console](https://login.tailscale.com/admin/machines), confirme **PC** e **VPS** na mesma rede.

Anote o host MagicDNS do PC (ex. `ramon-notebook`) ou o IP `100.x.y.z`:

```powershell
tailscale ip -4
```

## 2. validator-api no PC

Igual ao [local-windows.md](local-windows.md): `.env`, `doctor`, depois:

```powershell
cd validator-api
.\scripts\start-local.ps1
```

No `.env` use:

```env
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8765
GITHUB_WEBHOOK_SECRET=...   # igual ao webhook de DEV no GitHub
```

`0.0.0.0` permite que a VPS alcance o serviço pela interface Tailscale (não só `127.0.0.1`).

### Firewall Windows (se o health falhar da VPS)

PowerShell **como administrador** (regra só para rede privada):

```powershell
New-NetFirewallRule -DisplayName "validator-api 8765" `
  -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow `
  -Profile Private
```

Teste **da VPS** (substitua IP ou MagicDNS):

```bash
curl -sS "http://100.x.y.z:8765/health"
# ou: curl -sS "http://ramon-notebook.tailXXXX.ts.net:8765/health"
```

Deve retornar `ok`.

## 3. Caddy na VPS (subdomínio de dev)

Exemplo em [`deploy/Caddyfile.tailscale-dev`](../deploy/Caddyfile.tailscale-dev).

1. Troque `validador-dev.example.com` pelo seu DNS (A/AAAA → IP público da VPS).
2. Troque o upstream pelo **IP Tailscale do PC** ou MagicDNS (`nome.tailnet.ts.net`).
3. Recarregue Caddy (`systemctl reload caddy` ou como você já usa).

Teste público:

```bash
curl -sS "https://validador-dev.seudominio.com/health"
```

## 4. Webhook no GitHub (ambiente dev)

No repo **esimples-api** (ou crie um webhook **só para testes**):

| Campo | Valor |
|--------|--------|
| Payload URL | `https://validador-dev.seudominio.com/webhook` |
| Secret | mesmo `GITHUB_WEBHOOK_SECRET` do `.env` local |
| Events | **Pull requests** |

Push na PR → **Recent Deliveries** `202` → terminal local `[webhook] ... -> fila`.

Quando subir validador **na VPS**, aponte o webhook de **produção** para `https://validador.seudominio.com/webhook` (container), não para o PC.

## 5. Dia a dia

| O que manter ligado | Obrigatório para webhook automático |
|---------------------|-------------------------------------|
| Tailscale no PC e na VPS | Sim |
| `validator-api serve` no PC | Sim |
| Caddy na VPS | Sim |
| ngrok | Não |

PC dormindo ou Tailscale desligado → GitHub recebe erro até voltar (igual ngrok caído).

## 6. Segurança

- Webhook continua protegido por **HMAC** (`GITHUB_WEBHOOK_SECRET`).
- Porta `8765` no PC só precisa ser acessível na **tailnet**, não na internet (Caddy é a única entrada pública).
- Evite `tailscale funnel` para `/webhook` sem avaliar exposição; o modelo recomendado aqui é **VPS → tailnet → PC**.

## Problemas comuns

| Sintoma | O que verificar |
|---------|------------------|
| `502` no GitHub | `serve` parado, PC offline, IP MagicDNS errado no Caddy |
| Timeout da VPS → PC | `WEBHOOK_HOST=0.0.0.0`, firewall Windows |
| `401` no delivery | Secret GitHub ≠ `.env` |
| Caddy bate na prod | Host `validador-dev` deve apontar ao PC; prod ao `localhost:8765` do container |
