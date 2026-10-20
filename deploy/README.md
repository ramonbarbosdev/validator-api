# Deploy validator-api (VPS Linux)

> **CD (recomendado):** Docker + GHCR — [`github-actions/README.md`](github-actions/README.md) (mesmo padrao do `esimples-api`).

## Layout sugerido (bare metal)

```text
/opt/esimples-api          # REPO_ROOT
/opt/cursor-api-validator-java   # CURSOR_API_VALIDATOR_ROOT
/opt/validator-api           # este repo + .venv + .env
```

## Passos

1. Clonar os três repositórios.
2. `python3 -m venv /opt/validator-api/.venv && pip install -e /opt/validator-api`
3. `cp env.example .env` e preencher secrets (`RUNNER_API_TOKEN` obrigatório em produção).
4. `validator-api doctor`
5. Copiar `deploy/systemd/validator-api.service` para `/etc/systemd/system/`, ajustar `User` e paths.
6. `systemctl enable --now validator-api`
7. Caddy/nginx com TLS apontando para `localhost:8765` (ver `Caddyfile`).
8. GitHub webhook: `https://validador.example.com/webhook`, evento **Pull requests**.

**Dev local com webhook (sem ngrok):** PC + VPS na mesma tailnet — [`docs/local-tailscale.md`](../docs/local-tailscale.md) e `Caddyfile.tailscale-dev`.

## Logs

```bash
journalctl -u validator-api -f
```
