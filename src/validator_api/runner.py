"""Valida uma PR (checkout, install, agente, comentario na PR)."""
from __future__ import annotations

import base64
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from validator_api.config import PrReviewConfig
from validator_api.gate import should_validate
from validator_api.github import (
    fetch_pr,
    resolve_token,
    sync_block_label,
    upsert_review_comment,
    upsert_validation_started_comment,
)
from validator_api.state import get_validated_sha, load_state, mark_validated


def _phase(name: str, pr_number: int) -> None:
    try:
        from validator_api.queue import get_queue

        get_queue().set_phase(name, pr_number)
    except Exception:
        pass


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def _checkout_pr(
    app_dir: Path,
    repo: str,
    pr_number: int,
    token: str,
) -> None:
    if shutil.which("gh"):
        _run(
            ["gh", "pr", "checkout", str(pr_number), "--repo", repo, "--force"],
            cwd=app_dir,
        )
        return

    if not shutil.which("git"):
        raise RuntimeError(
            "Instale GitHub CLI (`gh`) ou Git no PATH para fazer checkout da PR."
        )

    local_ref = f"pr-review-{pr_number}"
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
    auth_header = f"AUTHORIZATION: basic {basic}"
    git_auth = ["-c", f"http.extraheader={auth_header}"]
    print(f"PR #{pr_number}: checkout via git (gh nao encontrado)…")
    _run(
        ["git", *git_auth, "fetch", "--force", "origin", f"pull/{pr_number}/head"],
        cwd=app_dir,
    )
    _run(["git", "checkout", "-B", local_ref, "FETCH_HEAD"], cwd=app_dir)


def _resolve_repo(cfg: PrReviewConfig) -> str:
    if cfg.repository and "/" in cfg.repository:
        return cfg.repository
    if not shutil.which("gh"):
        raise RuntimeError("Defina GITHUB_REPOSITORY ou instale `gh`.")
    out = subprocess.check_output(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        text=True,
        cwd=str(cfg.app_dir),
    ).strip()
    if not out:
        raise RuntimeError("Defina GITHUB_REPOSITORY.")
    return out


def run_validation(cfg: PrReviewConfig, pr_number: int, *, force: bool = False) -> int:
    _phase("buscando PR no GitHub", pr_number)
    token = resolve_token()
    repo = _resolve_repo(cfg)
    pr = fetch_pr(repo, pr_number, token)
    sha = (pr.get("head") or {}).get("sha") or ""
    pr_for_gate = {
        "isDraft": pr.get("draft"),
        "labels": [{"name": x["name"]} for x in (pr.get("labels") or [])],
    }
    ok, reason = should_validate(
        pr_for_gate,
        block_label=cfg.block_label,
        require_label=cfg.require_label,
        manual=force,
    )
    if not ok:
        print(f"PR #{pr_number}: pulando ({reason}).")
        return 0

    state = load_state(cfg.state_path)
    if not force and sha and get_validated_sha(state, pr_number) == sha:
        print(
            f"PR #{pr_number}: SHA {sha[:12]} ja validado — pulando "
            f"(use --force ou novo commit).",
            flush=True,
        )
        _phase("pulando (SHA ja validado)", pr_number)
        return 0

    print(f"PR #{pr_number}: validando ({reason}) @ {sha[:12]}…")

    _phase("comentario de inicio na PR", pr_number)
    try:
        upsert_validation_started_comment(
            repo,
            pr_number,
            token,
            sha=sha,
            pr_html_url=pr.get("html_url") or "",
        )
    except RuntimeError as e:
        print(f"PR #{pr_number}: aviso — comentario de inicio falhou: {e}", flush=True)

    _phase("checkout", pr_number)
    _checkout_pr(cfg.app_dir, repo, pr_number, token)

    _phase("install validador", pr_number)
    install_ps1 = cfg.validator_root / "install" / "install.ps1"
    install_sh = cfg.validator_root / "install" / "install.sh"
    if sys.platform == "win32" and install_ps1.is_file():
        _run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(install_ps1),
                "-Target",
                str(cfg.app_dir),
                "-Stack",
                cfg.stack,
            ],
            cwd=cfg.app_dir,
        )
    elif install_sh.is_file():
        _run(["bash", str(install_sh), str(cfg.app_dir), cfg.stack], cwd=cfg.app_dir)
    else:
        raise RuntimeError(f"Install nao encontrado em {cfg.validator_root}")

    env = os.environ.copy()
    env["REPO_ROOT"] = str(cfg.app_dir)
    env["GITHUB_REPOSITORY"] = repo
    env["GITHUB_BASE_REF"] = cfg.base_branch
    env["PR_NUMBER"] = str(pr_number)
    env["PR_HTML_URL"] = pr.get("html_url") or ""
    env.setdefault("CURSOR_VALIDATOR_RUNTIME", "cloud")
    env.setdefault("CURSOR_VALIDATOR_STRICT_REPORT", "1")

    ci = cfg.validator_root / "scripts" / "ci-api-validator.py"
    validate = cfg.validator_root / "scripts" / "validate-api-validator-report.py"
    wsl_ci = cfg.validator_root / "scripts" / "ci-api-validator-cloud-wsl.ps1"

    _phase("agente (cloud/local)", pr_number)
    if sys.platform == "win32" and wsl_ci.is_file() and env.get("CURSOR_VALIDATOR_RUNTIME") == "cloud":
        _run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(wsl_ci),
                "-ValidatorRoot",
                str(cfg.validator_root),
                "-RepoRoot",
                str(cfg.app_dir),
            ],
            cwd=cfg.app_dir,
            env=env,
        )
    else:
        _run([sys.executable, str(ci)], cwd=cfg.app_dir, env=env)

    _phase("validando relatorio", pr_number)
    _run([sys.executable, str(validate)], cwd=cfg.app_dir, env=env)

    _phase("publicando comentario na PR", pr_number)
    report_path = cfg.app_dir / "api-validator-report.md"
    if not report_path.is_file():
        print("Relatorio nao gerado.", file=sys.stderr)
        return 2
    report_body = report_path.read_text(encoding="utf-8")
    upsert_review_comment(repo, pr_number, report_body, token)
    sync_block_label(repo, pr_number, report_body, cfg.block_label, token)

    if sha:
        mark_validated(cfg.state_path, pr_number, sha)
    print(f"PR #{pr_number}: concluido.")
    return 0
