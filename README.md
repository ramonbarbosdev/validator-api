# validator-api

Serviço HTTP (webhook GitHub), fila e CLI para validar PRs com o pacote [cursor-api-validator-java](https://github.com/gpi-organizacao/cursor-api-validator-java).

UI desktop (React + Electron): repositório **[validator-front](https://github.com/gpi-organizacao/validator-front)**.

## Pré-requisitos

| Item | Uso |
|------|-----|
| Clone **esimples-api** | `REPO_ROOT` |
| Clone **cursor-api-validator-java** | `CURSOR_API_VALIDATOR_ROOT` |
| `CURSOR_API_KEY` | Agente Cursor (cloud) |
| `GITHUB_TOKEN` | API GitHub, checkout, comentário na PR |
| Python 3.10+ | Runner |
| Git | Checkout (ou `gh`) |
| WSL (Windows) | Agente cloud via `ci-api-validator-cloud-wsl.ps1` |

## Instalação

```powershell
cd validator-api
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
copy env.example .env
# edite .env
validator-api doctor
validator-api serve
```

Linux (VPS):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp env.example .env
validator-api doctor
validator-api serve
```

## CLI

| Comando | Descrição |
|---------|-----------|
| `validator-api serve` | Webhook + worker |
| `validator-api run --pr 123` | Valida uma PR |
| `validator-api run --pr 123 --force` | Ignora SHA já validado |
| `validator-api doctor` | Checagens de ambiente |
| `validator-api poll` | PRs com commit novo (dry-run, requer `gh`) |
| `validator-api poll --run` | Executa validação |

## API HTTP

Ver [docs/API.md](docs/API.md).

- `GET /health` — público
- `GET /status` e `GET /api/v1/status` — fila (Bearer se `RUNNER_API_TOKEN`)
- `POST /webhook` — GitHub (assinatura `GITHUB_WEBHOOK_SECRET`)
- `POST /api/v1/validate` — `{"pr_number": 123, "force": false}`

## Deploy na VPS (Docker + GHCR)

**Somente produção:** push em `main` → imagem **ghcr.io** → SSH → `docker run` (`network-esimples`, porta **8765**).

Guia: [`deploy/github-actions/README.md`](deploy/github-actions/README.md)

Alternativa sem Docker: [`deploy/README.md`](deploy/README.md) (systemd).

## ngrok (dev local)

```bash
ngrok http 8765
```

Payload URL: `https://....ngrok-free.app/webhook`
