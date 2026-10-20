# API REST — validator-api

Base URL: `http://host:8765` (ou HTTPS na VPS).

## Autenticação

Se `RUNNER_API_TOKEN` estiver definido no `.env`:

```http
Authorization: Bearer <RUNNER_API_TOKEN>
```

Rotas protegidas: `GET /status`, `GET /api/v1/status`, `POST /api/v1/validate`.

`/health` e `POST /webhook` (com assinatura GitHub) não usam esse token.

## Endpoints

### `GET /health`

Resposta: `200`, corpo `ok`.

### `GET /status` | `GET /api/v1/status`

Resposta JSON:

```json
{
  "ok": true,
  "repository": "org/esimples-api",
  "current": null,
  "pending": [],
  "pending_count": 0,
  "recent": []
}
```

`current` quando há PR em execução inclui `phase`, `phase_since`, `head_sha`.

### `POST /webhook`

Headers GitHub: `X-GitHub-Event`, `X-Hub-Signature-256`, `Content-Type: application/json`.

Resposta `202`:

```json
{
  "ok": true,
  "queued": true,
  "event": "pull_request/synchronize",
  "pr": 430,
  "queue_position": 1,
  "pending_count": 0
}
```

Ou ignorado:

```json
{
  "ok": true,
  "queued": false,
  "ignored": true,
  "reason": "aguardando label `validar-api`"
}
```

### `POST /api/v1/validate`

Corpo:

```json
{
  "pr_number": 430,
  "force": false
}
```

Resposta `202` com `queued: true` (mesmo formato da fila).

## CORS

Não habilitado por padrão. **validator-front** em desktop chama a API via HTTP cliente nativo (sem browser CORS).
