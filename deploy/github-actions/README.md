# GitHub Actions + Docker — somente produção

Fluxo:

```text
git push main (ou workflow_dispatch) → build → GHCR → SSH VPS → docker run
```

Workflow: [`.github/workflows/docker.yml`](../../.github/workflows/docker.yml).

**Não há homolog** — apenas branch `main` e environment GitHub **`prod`**.

## Produção na VPS

| Item | Valor |
|------|--------|
| Container | `validator-api` |
| Porta host | **8765** → 8765 no container |
| Env no servidor | `/home/app/validator-api.env` |
| Clone API (checkout PR) | `/home/app/esimples-api` |
| Pacote validador | `/home/app/cursor-api-validator-java` |
| Rede Docker | `network-esimples` |

## Secrets (mesmos do esimples-api)

| Secret | Descrição |
|--------|-----------|
| `SERVER_HOST` | VPS |
| `SERVER_USER` | SSH |
| `SERVER_SSH_KEY` | chave privada |
| `SERVER_PORT` | SSH |

Configure o environment **`prod`** no repositório validator-api (opcional: aprovação manual).

## Preparar VPS (uma vez)

```bash
sudo mkdir -p /home/app
sudo git clone https://github.com/gpi-organizacao/esimples-api.git /home/app/esimples-api
sudo git clone https://github.com/gpi-organizacao/cursor-api-validator-java.git /home/app/cursor-api-validator-java
```

`/home/app/validator-api.env` (paths **dentro** do container):

```env
GITHUB_REPOSITORY=gpi-organizacao/esimples-api
REPO_ROOT=/data/esimples-api
CURSOR_API_VALIDATOR_ROOT=/data/cursor-api-validator-java
GITHUB_WEBHOOK_SECRET=...
RUNNER_API_TOKEN=...
CURSOR_API_KEY=...
GITHUB_TOKEN=...
GITHUB_BASE_REF=develop
```

Webhook GitHub: `https://seu-dominio/webhook` → proxy para `localhost:8765`.

Imagem: `ghcr.io/gpi-organizacao/validator-api:prod-<sha>` e tag `prod-latest`.

## Build local

```bash
docker build -t validator-api:local .
docker run --rm -p 8765:8765 --env-file .env \
  -v /path/esimples-api:/data/esimples-api \
  -v /path/cursor-api-validator-java:/data/cursor-api-validator-java:ro \
  -e REPO_ROOT=/data/esimples-api \
  -e CURSOR_API_VALIDATOR_ROOT=/data/cursor-api-validator-java \
  validator-api:local
```
