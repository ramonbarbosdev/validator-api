#!/usr/bin/env python3
"""Backtest offline das regras estaticas sobre intervalos `base..head` de um repo local.

Para cada intervalo cria um worktree destacado em `head` e um ref temporario
`refs/remotes/origin/<REF>` em `base`, roda o motor e remove ambos. Nao faz fetch nem push.

Uso:
    python pack/scripts/backtest.py --repo ../esimples-api --range develop~20..develop [--range a..b] [--json saida.json]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_static_checks import run_static_checks  # noqa: E402

BACKTEST_REF = "__backtest_base"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout.strip()


def parse_range(intervalo: str) -> tuple[str, str]:
    """Separa `base..head` (ou `base...head`) em (base, head)."""
    base, sep, head = intervalo.partition("...") if "..." in intervalo else intervalo.partition("..")
    if not sep or not base or not head:
        raise ValueError(f"intervalo invalido: {intervalo!r} (esperado base..head)")
    return base, head


def run_range(repo: Path, intervalo: str) -> dict:
    """Roda o motor no diff `base...head` e devolve o resultado de `run_static_checks` com o intervalo."""
    base, head = parse_range(intervalo)
    base_sha = _git(repo, "rev-parse", "--verify", f"{base}^{{commit}}")
    head_sha = _git(repo, "rev-parse", "--verify", f"{head}^{{commit}}")
    ref = f"refs/remotes/origin/{BACKTEST_REF}"
    with tempfile.TemporaryDirectory(prefix="backtest-") as tmp:
        arvore = Path(tmp) / "wt"
        _git(repo, "worktree", "add", "--detach", "-q", str(arvore), head_sha)
        try:
            _git(repo, "update-ref", ref, base_sha)
            resultado = run_static_checks(BACKTEST_REF, arvore)
        finally:
            subprocess.run(["git", "-C", str(repo), "update-ref", "-d", ref], capture_output=True)
            subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(arvore)], capture_output=True)
    return {"intervalo": intervalo, **resultado}


def tabela(resultados: list[dict]) -> str:
    """Tabela Markdown: uma linha por regra, uma coluna por intervalo e o total."""
    contagens = [Counter(a["id"] for a in r["achados"]) for r in resultados]
    regras = sorted(set().union(*contagens)) if contagens else []
    cab = ["Regra", *(r["intervalo"] for r in resultados), "Total"]
    linhas = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for regra in regras:
        valores = [c.get(regra, 0) for c in contagens]
        linhas.append("| " + " | ".join([regra, *map(str, valores), str(sum(valores))]) + " |")
    totais = [sum(c.values()) for c in contagens]
    linhas.append("| " + " | ".join(["**Total**", *map(str, totais), str(sum(totais))]) + " |")
    falhas = [f"{r['intervalo']}: {f['id']} - {f['erro']}" for r in resultados for f in r["falhas_de_regra"]]
    if falhas:
        linhas += ["", "Falhas de regra:", *(f"- {f}" for f in falhas)]
    return "\n".join(linhas) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path("."), help="repo git local (default: .)")
    parser.add_argument("--range", dest="ranges", action="append", required=True, help="base..head (repetivel)")
    parser.add_argument("--json", type=Path, help="grava os achados completos neste arquivo")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    resultados = [run_range(repo, r) for r in args.ranges]
    print(tabela(resultados), end="")
    if args.json:
        args.json.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
