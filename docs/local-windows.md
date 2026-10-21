# Dev local (Windows)

Foco: validar PR do **esimples-api** (ou outra API Java) na sua máquina, sem VPS.

## O que roda onde

| Processo | Obrigatório? | Função |
|----------|--------------|--------|
| `validator-api serve` | Sim (webhook ou fila) | HTTP `:8765`, worker da fila |
| **Tailscale + Caddy na VPS** (recomendado) | Para **webhook do GitHub** com URL fixa | Ver [local-tailscale.md](local-tailscale.md) |
| `ngrok http 8765` | Alternativa ao Tailscale | URL pública → seu PC |
| `validator-api run --pr N` | Alternativa ao webhook | Valida uma PR manualmente |
| `validator-front` (`npm run dev`) | Opcional | UI; proxy `/validator-api` → `8765` |

O **esimples-api** não precisa estar rodando como Spring Boot. O validador só precisa do **clone git** com `pom.xml` (`REPO_ROOT`) para checkout da branch da PR.

## 1. Uma vez: ambiente

```powershell
cd C:\Users\Ramon\Documents\dev\Java\validator-api
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
pip install -r pack\scripts\requirements-ci.txt
copy env.example .env
```

Edite `.env`:

| Variável | Exemplo local |
|----------|----------------|
| `GITHUB_REPOSITORY` | `gpi-organizacao/esimples-api` |
| `REPO_ROOT` | `C:\Users\Ramon\Documents\dev\Java\esimples-api` |
| `GITHUB_TOKEN` | PAT com repo (ou `gh auth login` + token no env) |
| `CURSOR_API_KEY` | API Cursor (agente cloud) |
| `GITHUB_WEBHOOK_SECRET` | Mesmo secret do webhook no GitHub (se usar ngrok) |
| `GITHUB_BASE_REF` | `develop` |

**Não** defina `CURSOR_API_VALIDATOR_ROOT` em dev — o padrão é `pack/` dentro deste repo.

Se você já tinha `cursor-api-validator-java\scripts\.env.pr-review`, copie para `validator-api\.env` e remova a linha `CURSOR_API_VALIDATOR_ROOT=...`.

```powershell
validator-api doctor
```

No Windows o agente cloud usa WSL (`pack\scripts\ci-api-validator-cloud-wsl.ps1`). Se faltar distro/WSL, rode `pack\scripts\install-wsl-prereqs.ps1` uma vez.

## 2. Subir o serviço

```powershell
.\scripts\start-local.ps1
# ou: validator-api serve   (com .venv ativo e cwd = validator-api)
```

Teste: [http://127.0.0.1:8765/health](http://127.0.0.1:8765/health) → `ok`.

## 3. Validar sem ngrok (mais simples)

Com o `serve` rodando (worker ativo) **ou** só para um teste pontual:

```powershell
validator-api run --pr 123
```

Faz checkout da PR em `REPO_ROOT`, roda o pacote Cursor e publica comentário na PR.

## 4. Webhook automático (Tailscale + VPS)

Guia completo: **[local-tailscale.md](local-tailscale.md)**.

Resumo: Tailscale no PC e na VPS → Caddy em `validador-dev.seudominio.com` → IP Tailscale do PC `:8765` → webhook GitHub nessa URL.

```powershell
.\scripts\start-local.ps1
.\scripts\tailscale-dev-check.ps1
```

### Alternativa: ngrok

1. `validator-api serve` + `ngrok http 8765`
2. Payload URL: `https://xxxx.ngrok-free.app/webhook` (muda ao reiniciar o ngrok free)

## 5. UI (opcional)

```powershell
cd ..\validator-front
npm install
npm run dev
```

Abra a URL do Vite; o proxy encaminha `/validator-api` para `localhost:8765`.

## 6. Labels (opcional)

| Env | Efeito |
|-----|--------|
| `API_VALIDATOR_REQUIRE_LABEL=validar-api` | Só enfileira PR com essa label |
| `API_VALIDATOR_BLOCK_LABEL` | Com a label, webhook ignora; remover a label reenfileira validação (mesmo commit) |

## Problemas comuns

| Sintoma | Causa provável |
|---------|----------------|
| Webhook 401 | Secret diferente entre GitHub e `.env` |
| Nada na fila | Draft, label exigida ausente, ou evento não é Pull request |
| `REPO_ROOT sem pom.xml` | Path errado no `.env` |
| Doctor falha WSL | Instalar WSL + prereqs para agente cloud no Windows |
| Porta em uso | Outro `serve` ou processo na `8765` — mate o processo antigo |
