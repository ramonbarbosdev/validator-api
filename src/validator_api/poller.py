"""Detecta PR com commit novo (alternativa ao webhook)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

from validator_api.config import PrReviewConfig, load_env_file
from validator_api.gate import should_validate
from validator_api.runner import run_validation
from validator_api.state import get_validated_sha, load_state, mark_validated


def _gh_json(args: list[str], cwd: str | None = None) -> Any:
    out = subprocess.check_output(["gh", *args], text=True, cwd=cwd)
    return json.loads(out) if out.strip() else None


def _resolve_repository(cfg: PrReviewConfig) -> str:
    if cfg.repository and "/" in cfg.repository:
        return cfg.repository
    slug = _gh_json(
        ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        cwd=str(cfg.app_dir),
    )
    if not slug:
        raise SystemExit("Defina GITHUB_REPOSITORY ou rode com `gh` na pasta do app.")
    return str(slug).strip()


def list_open_prs(repo: str, base: str) -> list[dict[str, Any]]:
    return _gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--base",
            base,
            "--state",
            "open",
            "--json",
            "number,headRefOid,isDraft,labels,title",
        ]
    )


def pending_prs(cfg: PrReviewConfig) -> list[tuple[dict[str, Any], str]]:
    repo = _resolve_repository(cfg)
    state = load_state(cfg.state_path)
    pending: list[tuple[dict[str, Any], str]] = []

    for pr in list_open_prs(repo, cfg.base_branch):
        num = pr["number"]
        sha = pr.get("headRefOid") or ""
        ok, reason = should_validate(
            pr,
            block_label=cfg.block_label,
            require_label=cfg.require_label,
        )
        if not ok:
            continue
        last = get_validated_sha(state, num)
        if last == sha:
            continue
        pending.append((pr, f"novo commit: {last or '(nunca)'} -> {sha[:12]}… ({reason})"))

    return pending


def _which_gh() -> bool:
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False


def run_poller(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Poll PRs por commit novo")
    parser.add_argument("--run", action="store_true", help="Executa validacao para cada PR pendente")
    parser.add_argument("--pr", type=int, default=0, help="So esta PR")
    args = parser.parse_args(argv)

    if not _which_gh():
        print("Instale GitHub CLI (`gh`) e `gh auth login`.", file=sys.stderr)
        return 1

    load_env_file()
    cfg = PrReviewConfig.from_env()
    repo = _resolve_repository(cfg)

    if args.pr:
        pr = _gh_json(
            ["pr", "view", str(args.pr), "--repo", repo, "--json", "number,headRefOid,isDraft,labels,title"]
        )
        items = [(pr, "disparo manual --pr")]
    else:
        items = pending_prs(cfg)

    if not items:
        print("Nenhuma PR pendente de validacao.")
        return 0

    for pr, msg in items:
        n = pr["number"]
        sha = pr.get("headRefOid") or ""
        print(f"PR #{n}: {msg}")
        if not args.run:
            continue
        rc = run_validation(cfg, n)
        if rc == 0 and sha:
            mark_validated(cfg.state_path, n, sha)
        elif rc != 0:
            print(f"  Runner falhou (exit {rc}).", file=sys.stderr)
            return rc

    if not args.run:
        print("\nDry-run. Rode com --run para validar.")
    return 0
