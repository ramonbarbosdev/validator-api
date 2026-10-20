#!/usr/bin/env python3
"""Roda o api-validator (relatorio). CURSOR_API_KEY + install local ou modo cloud."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from pr_human_comments import load_pr_discussion_markdown, write_sidecar  # noqa: E402
from report_public import strip_conclusion_section  # noqa: E402

from cursor_sdk import (
    Agent,
    AgentOptions,
    CloudAgentOptions,
    CloudRepository,
    CursorAgentError,
    LocalAgentOptions,
)


def load_env_file(repo_root: Path) -> None:
    """Carrega .env do projeto (nao sobrescreve variavel ja definida no shell)."""
    env_file = repo_root / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def git_output(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return None


def normalize_github_url(remote: str) -> str:
    remote = remote.strip()
    if remote.startswith("https://") or remote.startswith("http://"):
        return remote.removesuffix(".git")
    m = re.match(r"git@github\.com:(.+?)(?:\.git)?$", remote)
    if m:
        return f"https://github.com/{m.group(1)}"
    if "/" in remote and not remote.startswith("git"):
        return f"https://github.com/{remote.removeprefix('/')}".removesuffix(".git")
    raise ValueError(f"Remote Git nao reconhecido: {remote}")


def resolve_api_repo_url(root: Path) -> str:
    explicit = os.environ.get("GITHUB_REPOSITORY_URL", "").strip()
    if explicit:
        return explicit.removesuffix(".git")
    slug = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if slug:
        return f"https://github.com/{slug.removeprefix('/')}"
    remote = git_output(root, "remote", "get-url", "origin")
    if not remote:
        raise RuntimeError(
            "Defina GITHUB_REPOSITORY ou configure git remote origin para modo cloud."
        )
    return normalize_github_url(remote)


def validator_repo_url() -> str:
    raw = os.environ.get(
        "VALIDATOR_REPO", "ramonbarbosdev/cursor-api-validator-java"
    ).strip()
    if raw.startswith("http"):
        return raw.removesuffix(".git")
    return f"https://github.com/{raw.removeprefix('/')}".removesuffix(".git")


def resolve_validator_starting_ref() -> str | None:
    """SHA ou ref do pacote validador para segundo repo cloud (opcional)."""
    explicit = os.environ.get("VALIDATOR_REF", "").strip()
    if explicit and explicit.lower() not in ("auto", "main"):
        return explicit
    pinned = os.environ.get("VALIDATOR_PIN_SHA", "").strip()
    if pinned:
        return pinned
    url = validator_repo_url()
    try:
        out = subprocess.check_output(
            ["git", "ls-remote", f"{url}.git", "HEAD"],
            text=True,
            timeout=90,
            stderr=subprocess.DEVNULL,
        )
        sha = out.split()[0] if out.strip() else ""
        return sha or None
    except (subprocess.CalledProcessError, OSError, ValueError):
        return None


def attach_validator_cloud_repo() -> bool:
    return os.environ.get("CURSOR_VALIDATOR_ATTACH_VALIDATOR_REPO", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def resolve_starting_ref(root: Path) -> str:
    for key in ("GITHUB_SHA", "CURSOR_VALIDATOR_STARTING_REF"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    head = git_output(root, "rev-parse", "HEAD")
    if head:
        return head
    raise RuntimeError("Nao foi possivel obter SHA/ref para modo cloud.")


def resolve_runtime() -> str:
    explicit = os.environ.get("CURSOR_VALIDATOR_RUNTIME", "").strip().lower()
    if explicit in ("cloud", "local"):
        return explicit
    if sys.platform == "win32" and os.environ.get("CURSOR_VALIDATOR_FORCE_LOCAL") != "1":
        return "cloud"
    return "local"


def warn_cloud_push(root: Path, starting_ref: str) -> None:
    branch = git_output(root, "branch", "--show-current")
    if not branch:
        return
    on_origin = git_output(root, "rev-parse", f"origin/{branch}")
    head = git_output(root, "rev-parse", "HEAD")
    if not on_origin:
        print(
            f"AVISO: branch '{branch}' nao existe em origin. "
            "O agente cloud clona do GitHub — faca git push antes.",
            file=sys.stderr,
        )
        return
    if head and on_origin and head != on_origin:
        print(
            f"AVISO: HEAD local ({head[:8]}) != origin/{branch} ({on_origin[:8]}). "
            "Cloud usara starting_ref; push se quiser o commit local na revisao.",
            file=sys.stderr,
        )
    if head and starting_ref == head and on_origin and head != on_origin:
        print(
            "Dica: use CURSOR_VALIDATOR_STARTING_REF=origin/<branch> apos push, "
            "ou push e use o nome da branch como ref.",
            file=sys.stderr,
        )


def git_diff_names(root: Path, base: str) -> list[str]:
    for ref in (f"origin/{base}...HEAD", f"origin/{base}", "HEAD"):
        try:
            out = subprocess.check_output(
                ["git", "diff", "--name-only", ref],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            names = [ln.strip() for ln in out.splitlines() if ln.strip()]
            if names:
                return names
        except subprocess.CalledProcessError:
            continue
    return []


def build_prompt(
    root: Path,
    base: str,
    pr_label: str,
    stat: str,
    spec_line: str,
    *,
    cloud: bool,
    pr_discussion: str = "",
    changed_files: list[str] | None = None,
) -> str:
    agent_rel = ".cursor/agents/api-validator.md"
    validator_url = validator_repo_url()

    pin = os.environ.get("VALIDATOR_PIN_SHA", "").strip()
    pin_line = (
        f"Use o commit do pacote validador deste CI: `{pin}` (apos clone, `git checkout {pin}`).\n"
        if pin
        else ""
    )
    if cloud:
        prep = f"""Ambiente **cloud**: clone da API no GitHub (starting_ref).

**Obrigatorio antes da revisao** (nao altere src/ nem db/ da aplicacao):
1. `git clone {validator_url} /tmp/cursor-api-validator-java`
{pin_line}2. `bash /tmp/cursor-api-validator-java/install/install.sh "$(pwd)" java-spring-esimples`
3. Confirme que existe `{agent_rel}`; leia esse arquivo **inteiro** e siga precedencia, evidencia e veredito.
4. Use `.cursor/skills/revisao-api/SKILL.md`, `docs/validador/README.md`, `docs/validador/processo/nao-reportar.md` e regras `EV-*` em `.cursor/rules/` quando o diff tocar o assunto.
5. Se o diff tiver migration: `EV-PER-006` e `docs/padrao/banco.md` — dados/integridade primeiro; SQL nao pode quebrar a aplicacao na subida.


Cite **pelo menos dois caminhos** de arquivo do diff no relatorio (em Critico/Importante ou na Conclusao), ex. `src/main/java/.../Foo.java`.
Achado **Critico**/**Importante**: regra ou doc citada + evidencia (classe/metodo/linha ou trecho).
"""
    else:
        agent_file = root / agent_rel
        prep = f"""Leia e siga a risca o procedimento em:
{agent_file}

Tambem use .cursor/skills/revisao-api/SKILL.md, docs/validador/README.md e docs/validador/processo/nao-reportar.md quando aplicavel.

Cite **pelo menos dois caminhos** de arquivo do diff no relatorio (sem secao Resumo).
"""

    files_block = ""
    if changed_files:
        lines = "\n".join(f"- `{p}`" for p in changed_files[:35])
        files_block = f"\nArquivos alterados no diff (citar >=2 no relatorio):\n{lines}\n"

    discussion_block = ""
    discussion_rules = ""
    if pr_discussion.strip():
        discussion_rules = """
**Discussao humana na PR (bloco abaixo):** leia primeiro e trate como combinado de negocio (api-validator.md, secao Discussao na PR).
Nao reprove por padrao de vizinho se o comentario explica a intencao e o diff implementa o combinado (cite autor + trecho no codigo).
Seguranca critica e tenant critico (EV-SEC-*, EV-MTN-001/002/003) prevalecem sobre comentario.
Comentario promete comportamento que o diff nao entrega, ou diff contradiz comentario: achado com evidencia + referencia ao comentario.
"""
        discussion_block = f"\n{pr_discussion.strip()}\n"
    return f"""Voce e o revisor api-validator do esimples-api (Java Spring Boot).

{discussion_rules}

{prep}

Modo somente leitura na API: NAO altere arquivos de aplicacao (src/, db/, docs/ de dominio).

Escopo: {pr_label}, diff vs origin/{base}.
{spec_line}

Execute (somente leitura): git fetch origin {base}; git diff --stat origin/{base}...HEAD; git diff origin/{base}...HEAD nos arquivos relevantes.

Saida EXATAMENTE nesta ordem, com estes titulos markdown (copie literal):
## Critico
## Importante
## Melhoria / Ajuste
## Conclusao
Assuma front/consumidor da API. **Prioridade:** em auth/erros/validacao/listagem autenticada, varra **Critico** e **Importante** com docs/validador/critico/consumidor-api.md e docs/validador/importante/consumidor-api.md (loop de login, tenant, contrato quebrado, 401 vs 403, vazamento). So depois preencha **Melhoria / Ajuste** (docs/validador/melhoria-ajuste/consumidor-api.md) para polish que NAO impede o usuario de concluir a tarefa. Melhoria NAO altera a Conclusao.
Regra: qualquer item em Critico ou Importante (alem de `Nenhum.`) -> ultima linha `Conclusao: NAO APROVAVEL` (nunca APROVAVEL nem COM RESSALVAS).
So `Nenhum.` em Critico e Importante -> `Conclusao: APROVAVEL`.
No diff em service/controller/security: comentario // ou /* dentro de metodo -> **Importante** (EV-SVC-003); metodo publico novo sem JavaDoc -> **Importante** (EV-SVC-002); JavaDoc presente mas fora do padrao (docs/validador/melhoria-ajuste/javadoc.md) -> **Melhoria / Ajuste**.
Sem achado tecnico: Critico e Importante = `Nenhum.`; Melhoria / Ajuste = `Nenhum.` ou itens de UX de API / JavaDoc.

git diff --stat (referencia local do disparo):
{stat}
{files_block}{discussion_block}
"""


def write_report(root: Path, pr_label: str, base: str, pr: str, body: str) -> Path:
    report_path = root / "api-validator-report.md"
    header = f"<!-- review -->\n## Review ({pr_label})\n\n"
    if pr:
        header += f"_Base: `{base}` · disparo: push na PR_\n\n"
    full_text = header + body + "\n"
    report_path.write_text(full_text, encoding="utf-8")
    (root / "api-validator-report-public.md").write_text(
        strip_conclusion_section(full_text), encoding="utf-8"
    )
    return report_path


def main() -> int:
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    load_env_file(root)

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        env_file = root / ".env"
        if env_file.is_file():
            has_key = any(
                ln.strip().startswith("CURSOR_API_KEY=")
                for ln in env_file.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            )
            if not has_key:
                print(
                    f".env encontrado em {env_file} mas sem linha CURSOR_API_KEY=...",
                    file=sys.stderr,
                )
            else:
                print(
                    "CURSOR_API_KEY esta vazio no .env (valor apos o =).",
                    file=sys.stderr,
                )
        else:
            print(
                f"Crie {env_file} com: CURSOR_API_KEY=sua-chave",
                file=sys.stderr,
            )
        print(
            "Chave: Cursor Settings -> API. GitHub Actions: secret CURSOR_API_KEY.",
            file=sys.stderr,
        )
        return 1

    runtime = resolve_runtime()
    agent_file = root / ".cursor" / "agents" / "api-validator.md"
    if runtime == "local" and not agent_file.is_file():
        print(f"Falta install do validador: {agent_file}", file=sys.stderr)
        return 1

    base = os.environ.get("GITHUB_BASE_REF", "develop").removeprefix("origin/")
    pr = os.environ.get("PR_NUMBER", "").strip()
    pr_label = f"PR #{pr}" if pr else "PR"

    try:
        stat = subprocess.check_output(
            ["git", "diff", "--stat", f"origin/{base}...HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        stat = subprocess.check_output(
            ["git", "diff", "--stat", f"origin/{base}", "HEAD"],
            cwd=root,
            text=True,
        )

    spec_path = root / "docs" / "SPEC.md"
    if spec_path.is_file():
        spec_line = (
            "Existe docs/SPEC.md na branch: modo inteligente; "
            "escopo ampliado se a SPEC tiver Contrato HTTP (docs/validador/processo/escopo-e-rest.md)."
        )
    else:
        spec_line = "Sem docs/SPEC.md na branch: gate enxuto (somente git diff vs base)."

    pr_discussion = ""
    if pr.isdigit():
        pr_discussion = load_pr_discussion_markdown(int(pr))
        if pr_discussion:
            write_sidecar(root, int(pr), pr_discussion)

    changed_files = git_diff_names(root, base)

    model = os.environ.get("CURSOR_VALIDATOR_MODEL", "composer-2.5")
    prompt = build_prompt(
        root,
        base,
        pr_label,
        stat,
        spec_line,
        cloud=(runtime == "cloud"),
        pr_discussion=pr_discussion,
        changed_files=changed_files,
    )

    if runtime == "cloud":
        try:
            repo_url = resolve_api_repo_url(root)
        except (RuntimeError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 1
        starting_ref = resolve_starting_ref(root)
        warn_cloud_push(root, starting_ref)
        pr_url = os.environ.get("PR_HTML_URL", "").strip()
        if not pr_url and pr and os.environ.get("GITHUB_REPOSITORY"):
            pr_url = (
                f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/pull/{pr}"
            )
        print(
            f"Modo cloud: {repo_url} @ {starting_ref[:12]}...",
            file=sys.stderr,
        )
        repos = [
            CloudRepository(
                url=repo_url,
                starting_ref=starting_ref,
                pr_url=pr_url or None,
            )
        ]
        if attach_validator_cloud_repo():
            v_url = validator_repo_url()
            v_ref = resolve_validator_starting_ref()
            if v_ref:
                repos.append(CloudRepository(url=v_url, starting_ref=v_ref))
                print(
                    f"Cloud: anexando validador {v_url} @ {v_ref[:12]}...",
                    file=sys.stderr,
                )
            else:
                print(
                    "AVISO: CURSOR_VALIDATOR_ATTACH_VALIDATOR_REPO=1 mas sem VALIDATOR_REF/SHA; "
                    "somente repo da API.",
                    file=sys.stderr,
                )
        options = AgentOptions(
            api_key=api_key,
            model=model,
            cloud=CloudAgentOptions(
                repos=repos,
                skip_reviewer_request=True,
                auto_create_pr=False,
            ),
        )
    else:
        if sys.platform == "win32" and os.environ.get("CURSOR_VALIDATOR_FORCE_LOCAL") != "1":
            print(
                "No Windows use CURSOR_VALIDATOR_RUNTIME=cloud (padrao) ou "
                "CURSOR_VALIDATOR_FORCE_LOCAL=1 para tentar local.",
                file=sys.stderr,
            )
            return 3
        options = AgentOptions(
            api_key=api_key,
            model=model,
            local=LocalAgentOptions(cwd=str(root)),
        )

    try:
        result = Agent.prompt(prompt, options)
    except OSError as e:
        print(f"SDK bridge falhou: {e}", file=sys.stderr)
        if sys.platform == "win32" and runtime == "cloud":
            print(
                "No Windows o cursor-sdk usa bridge mesmo em cloud. "
                "Use scripts/ci-api-validator-cloud-wsl.ps1 (WSL) ou job ubuntu.",
                file=sys.stderr,
            )
        else:
            print(
                "Tente CURSOR_VALIDATOR_RUNTIME=cloud ou /api-validator no Cursor.",
                file=sys.stderr,
            )
        return 3
    except CursorAgentError as e:
        print(f"Falha ao iniciar agente: {e}", file=sys.stderr)
        return 1

    if result.status == "error":
        print(f"Run falhou: {result.id}", file=sys.stderr)
        return 2

    body = (result.result or "").strip()
    if not body:
        body = "_Validador nao retornou texto. Ver logs do workflow._"

    report_path = write_report(root, pr_label, base, pr, body)
    public_body = strip_conclusion_section(
        (root / "api-validator-report.md").read_text(encoding="utf-8")
    )
    print(public_body)
    print(f"\nSalvo em: {report_path} (publico: api-validator-report-public.md)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
