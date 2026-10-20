# GitHub Actions + Docker — somente produção

Fluxo: `git push main` → GHCR → SSH → `docker run`.

O **pacote validador** (`pack/`) vai **dentro da imagem** — não clone `cursor-api-validator-java` na VPS.

## VPS

| Item | Valor |
|------|--------|
| Container | `validator-api` |
| Porta | **8765** |
| Env | `/home/app/validator-api.env` |
| Volume | `/home/app/app-repo` → `/data/app` (clone **git** do repo da API) |

```bash
sudo git clone https://github.com/gpi-organizacao/esimples-api.git /home/app/app-repo
# ou qualquer outra API Java com pom.xml
```

`/home/app/validator-api.env`:

```env
GITHUB_REPOSITORY=gpi-organizacao/esimples-api
REPO_ROOT=/data/app
GITHUB_WEBHOOK_SECRET=...
RUNNER_API_TOKEN=...
CURSOR_API_KEY=...
GITHUB_TOKEN=...
GITHUB_BASE_REF=develop
# API_VALIDATOR_STACK=java-spring-esimples
```

Secrets: `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`, `SERVER_PORT`.

## Instalar regras no repo da API (dev)

```powershell
.\pack\install\install.ps1 -Target C:\path\sua-api -Stack java-spring-esimples
```
