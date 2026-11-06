#!/usr/bin/env python3
"""Executa o motor declarativo (pack/engine) e grava findings-estaticos.json sem derrubar a validacao."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

PACK_ROOT = Path(__file__).resolve().parent.parent
PADROES_PATH = PACK_ROOT / "rules" / "padroes.yaml"
FINDINGS_NAME = "findings-estaticos.json"
ENV_FLAG = "VALIDATOR_STATIC_CHECKS"


def static_checks_enabled() -> bool:
    """`VALIDATOR_STATIC_CHECKS` ligado por padrao; `0`, `false`, `no` ou `off` desligam."""
    raw = os.environ.get(ENV_FLAG, "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _empty_result() -> dict[str, Any]:
    return {
        "achados": [],
        "falhas_de_regra": [],
        "regras_executadas": [],
        "regras_inativas": [],
        "regras_llm_aplicaveis": [],
    }


def _motor():
    if str(PACK_ROOT) not in sys.path:
        sys.path.insert(0, str(PACK_ROOT))
    from engine import motor

    return motor


def run_static_checks(base: str, repo: Path, *, regras_path: Path | None = None) -> dict[str, Any]:
    """Roda o motor; catalogo invalido, dependencia ausente ou erro de diff viram `falhas_de_regra`."""
    resultado = _empty_result()
    try:
        motor = _motor()
        regras = motor.carregar_regras(regras_path or PADROES_PATH)
    except Exception as exc:
        resultado["falhas_de_regra"].append({"id": "motor", "erro": f"{type(exc).__name__}: {exc}"})
        return resultado

    erros = motor.validar_regras(regras)
    if erros:
        resultado["falhas_de_regra"].append({"id": "catalogo", "erro": "; ".join(erros)})
        return resultado

    try:
        resultado.update(motor.executar(base, str(repo), regras))
    except Exception as exc:
        resultado["falhas_de_regra"].append({"id": "motor", "erro": f"{type(exc).__name__}: {exc}"})
    return resultado


def write_findings(resultado: dict[str, Any], out_dir: Path) -> Path:
    """Grava o JSON em `<out_dir>/findings-estaticos.json`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / FINDINGS_NAME
    path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_findings(out_dir: Path) -> dict[str, Any] | None:
    """Le `findings-estaticos.json`; None se ausente ou invalido."""
    path = out_dir / FINDINGS_NAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def run_and_write(base: str, repo: Path, out_dir: Path | None = None) -> dict[str, Any]:
    """Roda e grava; erro ao gravar tambem nao propaga."""
    resultado = run_static_checks(base, repo)
    try:
        path = write_findings(resultado, out_dir or repo)
    except OSError as exc:
        print(f"AVISO: nao gravou {FINDINGS_NAME}: {exc}", file=sys.stderr)
        return resultado
    print(
        f"Checks estaticos: {len(resultado['achados'])} achado(s), "
        f"{len(resultado['falhas_de_regra'])} falha(s) de regra -> {path}",
        file=sys.stderr,
    )
    for falha in resultado["falhas_de_regra"]:
        print(f"  AVISO regra {falha['id']}: {falha['erro']}", file=sys.stderr)
    return resultado


def main(argv: list[str] | None = None) -> int:
    """Uso: run_static_checks.py <base> [repo] [saida]. Sempre sai 0."""
    args = list(sys.argv[1:] if argv is None else argv)
    base = (args[0] if args else os.environ.get("GITHUB_BASE_REF", "develop")).removeprefix("origin/")
    repo = Path(args[1] if len(args) > 1 else os.environ.get("REPO_ROOT", ".")).resolve()
    out_dir = Path(args[2]).resolve() if len(args) > 2 else repo
    run_and_write(base, repo, out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
