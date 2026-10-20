# validator-api

Serviço (webhook, fila, CLI) + **pacote Cursor** em [`pack/`](pack/) — regras, skill, `install`, agente CI.

Funciona com **qualquer** API Java/Spring: configure `GITHUB_REPOSITORY` e `REPO_ROOT` (clone git para checkout de PR).

UI: [validator-front](https://github.com/gpi-organizacao/validator-front) (React).

## Estrutura

| Pasta | Conteúdo |
|-------|----------|
| `pack/` | Ex-`cursor-api-validator-java`: `.cursor/`, `docs/`, `install/`, `stacks/`, `scripts/ci-api-validator.py` |
| `src/validator_api/` | Serviço HTTP e runner |

`CURSOR_API_VALIDATOR_ROOT` **opcional** — padrão é `pack/` (ou `/app/pack` no Docker).

## Dev local

Guia local: **[docs/local-windows.md](docs/local-windows.md)** · webhook com URL fixa (Tailscale + VPS): **[docs/local-tailscale.md](docs/local-tailscale.md)**.

```powershell
cd validator-api
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
pip install -r pack/scripts/requirements-ci.txt
copy env.example .env
# REPO_ROOT = clone do repo da API (ex. esimples-api)
validator-api doctor
.\scripts\start-local.ps1
```

Instalar regras no projeto da API:

```powershell
.\pack\install\install.ps1 -Target C:\path\sua-api -Stack java-spring-esimples
```

## CLI

| Comando | Descrição |
|---------|-----------|
| `validator-api serve` | Webhook + worker |
| `validator-api run --pr N` | Valida uma PR |
| `validator-api doctor` | Checagens de ambiente |

API: [docs/API.md](docs/API.md).

## Deploy produção (Docker + GHCR)

Push `main` → Actions → VPS. Pacote **já na imagem**; na VPS só volume do **repo da API** (`/home/app/app-repo` → `/data/app`).

[`deploy/github-actions/README.md`](deploy/github-actions/README.md)
