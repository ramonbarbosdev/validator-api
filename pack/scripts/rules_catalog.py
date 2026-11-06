#!/usr/bin/env python3
"""Leitura do catalogo de regras (pack/rules/catalog.yaml)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

PACK_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PACK_ROOT / "rules" / "catalog.yaml"

TIPOS = ("estatico", "semi", "semantico")
SEVERIDADES = ("CRITICO", "IMPORTANTE", "MELHORIA")
STATUS_ATIVO = "ativo"


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    """Retorna a lista de regras do catalogo YAML."""
    import yaml

    data = yaml.safe_load((path or CATALOG_PATH).read_text(encoding="utf-8")) or {}
    return list(data.get("regras") or [])


def rule_status(regra: dict[str, Any]) -> str:
    """Status efetivo: ausente com `check` equivale a `ativo`."""
    status = str(regra.get("status") or "").strip().lower()
    if status:
        return status
    return STATUS_ATIVO if regra.get("check") else ""


def check_path(regra: dict[str, Any], pack_root: Path | None = None) -> Path | None:
    """Caminho absoluto do script de check da regra, se declarado."""
    rel = regra.get("check")
    if not rel:
        return None
    return (pack_root or PACK_ROOT) / str(rel)


def active_static_rules(regras: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Regras `estatico` com check ativo, na ordem do catalogo."""
    return [
        r
        for r in regras
        if r.get("tipo") == "estatico" and r.get("check") and rule_status(r) == STATUS_ATIVO
    ]
