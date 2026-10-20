# Automação na PR sem GitHub Actions

O Actions dispara no evento `pull_request` → `synchronize` (novo commit). **Sem Actions**, você escolhe quem recebe esse evento.

## Como saber que há commit novo

A PR no GitHub tem sempre um **HEAD** (`headRefOid` = SHA do último commit da branch).

| Mecanismo | Como detecta | Precisa de URL pública? |
|-----------|----------------|-------------------------|
| **Polling** | A cada N minutos: `gh pr list` + comparar SHA com arquivo local | Não |
| **Webhook** | GitHub POST no seu servidor em cada `synchronize` | Sim (VPS + HTTPS ou túnel) |
| **Hook `post-push` local** | Só quando **você** faz `git push` | Não (não vê push de outras pessoas) |

Estado sugerido: `esimples-api/.api-validator-review/automation-state.json`

```json
{
  "prs": {
    "430": { "validated_sha": "abc123…", "at": "2026-03-20T12:00:00Z" }
  }
}
```

Se `headRefOid` ≠ `validated_sha` → há commit novo (ou PR nunca validada).

Script: `scripts/pr_review_poller.py` (dry-run ou `--run` quando o runner existir).

```powershell
$env:GITHUB_REPOSITORY = "org/esimples-api"
$env:REPO_ROOT = "C:\path\esimples-api"
py -3 ..\cursor-api-validator-java\scripts\pr_review_poller.py
```

Agende no **Agendador de Tarefas** (Windows) ou `cron` (Linux) a cada 2–5 minutos.

## Webhook (tempo quase real — como no SIPEC)

Guia completo: [`servidor-webhook.md`](servidor-webhook.md).

```powershell
.\scripts\start-pr-review-webhook.ps1
ngrok http 8765
```

Payload URL no GitHub: `https://....ngrok-free.app/webhook`

## Labels e comentários

- Gate: `API_VALIDATOR_REQUIRE_LABEL`, `API_VALIDATOR_BLOCK_LABEL` (env) — mesma lógica do workflow.
- Comentários humanos: `pr_human_comments.py` + `GITHUB_TOKEN` / `gh auth` no runner local.

## Desligar Actions

Remova ou desative `.github/workflows/api-validator-pr.yml` e use poller ou webhook na sua máquina/VPS.
