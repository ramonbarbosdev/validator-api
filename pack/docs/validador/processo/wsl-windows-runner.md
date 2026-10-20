# WSL no Windows — runner self-hosted e CI automático

No **Windows**, o `cursor-sdk` (Python nativo) falha ao subir o bridge (`WinError 10038`), **mesmo** com `CURSOR_VALIDATOR_RUNTIME=cloud`.

Para **GitHub Actions** com `runs-on: self-hosted` no PC Windows, o esimples-api chama `scripts/ci-api-validator-cloud-wsl.ps1`: o agente cloud roda **dentro do WSL** (Linux).

No **Cursor IDE** (`/api-validator`) ou `validate-pr-local-ide.cmd` **não** precisa WSL — só o fluxo automático via SDK no runner.

---

## Pré-requisitos

| Item | Motivo |
|------|--------|
| **Windows 10/11** com **WSL2** | Distribuição padrão: **Ubuntu** (22.04 ou 24.04) |
| `python3`, `python3-venv`, `python3-pip` | venv em `~/.cache/api-validator-ci-venv` (PEP 668 — sem `pip` no sistema) |
| `git` | diff e checkout (geralmente já vem no Ubuntu) |
| Acesso à internet no WSL | `pip install cursor-sdk` e API Cursor |

Opcional no runner Windows (`.env` em `actions-runner`):

```env
VALIDATOR_LOCAL_PATH=C:\Users\SEU_USUARIO\...\cursor-api-validator-java
```

---

## Instalação rápida (recomendado)

No **PowerShell** (Windows), na pasta deste repositório (`cursor-api-validator-java`):

```powershell
.\scripts\install-wsl-prereqs.ps1
```

Ou só dentro do **WSL**:

```bash
cd /mnt/c/caminho/para/cursor-api-validator-java
bash scripts/install-wsl-prereqs.sh
```

O script:

1. Instala pacotes Debian (`python3-venv`, `python3-pip`, `git`) se faltar.
2. Cria `~/.cache/api-validator-ci-venv` se não existir.
3. Instala `scripts/requirements-ci.txt` (`cursor-sdk`) no venv.

---

## Instalação manual (Ubuntu no WSL)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

python3 -m venv "$HOME/.cache/api-validator-ci-venv"
"$HOME/.cache/api-validator-ci-venv/bin/python" -m pip install -U pip
"$HOME/.cache/api-validator-ci-venv/bin/python" -m pip install -r /mnt/c/.../cursor-api-validator-java/scripts/requirements-ci.txt
```

Substitua o caminho do `requirements-ci.txt` pelo clone local do pacote validador.

---

## GitHub (esimples-api)

| Variable | Valor |
|----------|--------|
| `API_VALIDATOR_EXECUTOR` | `local` |
| `API_VALIDATOR_LOCAL_AI` | omitir ou `cloud` |

| Secret | Valor |
|--------|--------|
| `CURSOR_API_KEY` | chave Cursor API |

### Ligar o runner (atalho)

Na pasta do pacote validador (Windows):

```powershell
.\scripts\install-runner-desktop-shortcut.ps1 -RunnerHome C:\actions-runner
```

Isso cria **GitHub Actions Runner** na Área de Trabalho e define `ACTIONS_RUNNER_HOME` para o usuário.

Ou execute direto (janela aberta enquanto houver jobs):

```text
cursor-api-validator-java\scripts\start-actions-runner.cmd
```

Edite `ACTIONS_RUNNER_HOME` no `.cmd` se o runner não estiver em `C:\actions-runner`.

Runner online. Log esperado no Actions:

```text
Windows: executando api-validator (cloud) via WSL...
```

---

## Sem WSL

- **Automático na nuvem GitHub:** `API_VALIDATOR_EXECUTOR=cloud` (job `ubuntu-latest`).
- **Manual no Cursor:** modo `API_VALIDATOR_LOCAL_AI=ide` ou `validate-pr-local-ide.cmd` — sem SDK no runner.

---

## Problemas comuns

| Erro | Ação |
|------|------|
| `externally-managed-environment` | Use o venv (`install-wsl-prereqs.sh`), não `pip install` no sistema |
| `nao foi possivel criar venv` | `sudo apt install -y python3-venv python3-full` |
| `WSL nao encontrado` | `wsl --install` (Windows) e reinicie |
| `PY: command not found` | Atualize `ci-api-validator-cloud-wsl.ps1` (versão que monta bash sem expandir `$` no PowerShell) |
| `WinError 10038` no Windows | Esperado sem WSL; use `ci-api-validator-cloud-wsl.ps1` ou job cloud no GitHub |

---

Ver também: [`review-por-pr.md`](review-por-pr.md) (fluxo PR e CI).
