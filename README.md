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

## Validador híbrido (motor estático + LLM)

Fluxo de cada validação de PR:

1. `ci-api-validator.py` roda o motor declarativo (`pack/engine`, tree-sitter Java + extrator SQL) sobre as **linhas adicionadas** em `git diff origin/<base>...HEAD` e grava `findings-estaticos.json` no repo.
2. O prompt do agente recebe o bloco `## ACHADOS ESTATICOS CONFIRMADOS`: o LLM não reanalisa essas regras e foca nas semânticas.
3. `validate-api-validator-report.py` mescla no relatório os achados que o LLM omitiu (`merge_static_findings.py`, idempotente) e **recalcula a Conclusão em código** (Crítico ou Importante ⇒ `NAO APROVAVEL`).
4. `report_gate.needs_block_label` aplica o mesmo merge antes de decidir as labels.

Flag `VALIDATOR_STATIC_CHECKS` (padrão ligado; `0`/`false`/`no`/`off` desliga). Desligada, o prompt é idêntico ao legado (snapshot em `tests/snapshots/`). Falha do motor ou de uma regra vira `falhas_de_regra` no JSON e nunca derruba a validação.

| Arquivo | Papel |
|---------|-------|
| `pack/rules/padroes.yaml` | Regras executáveis pelo motor (tipos em `pack/engine/GUIA.md`) |
| `pack/rules/catalog.yaml` | Metadados de todas as regras EV-* (`tipo`, `status`, `check: rules/padroes.yaml#ID`) |
| `pack/scripts/run_static_checks.py` | Wrapper do motor + flag + `findings-estaticos.json` |
| `pack/scripts/merge_static_findings.py` | Merge no relatório + Conclusão calculada |
| `pack/scripts/backtest.py` | Backtest offline por intervalo de commits |

### Adicionar uma regra estática

1. Adicione a regra em `pack/rules/padroes.yaml` (id, tipo, severidade, arquivos, mensagem, como_corrigir).
2. No `catalog.yaml`, marque a regra como `tipo: estatico` e `check: rules/padroes.yaml#<ID>`. Para uma regra ainda não pronta, use `status: pendente`.
3. Crie `tests/fixtures/<ID>/ruim/` (deve disparar) e `tests/fixtures/<ID>/bom/` (não deve), com caminhos iguais aos do repo da API. O `test_fixtures.py` exige fixture para toda regra estática ativa.

### Testes e lint

```powershell
pip install -e ".[dev]"
pytest -q
ruff check .
```

O workflow `.github/workflows/ci.yml` roda os mesmos comandos em pull_request e push.

### Backtest

Mede quantos achados cada regra geraria em PRs passadas, sem rede (usa worktree temporário + ref local, ambos removidos ao final):

```powershell
python pack/scripts/backtest.py --repo ..\esimples-api --range origin/develop~30..origin/develop --json backtest.json
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
