#!/usr/bin/env python3
"""Leitura do catalogo de regras (pack/rules/catalog.yaml) e do catalogo do motor (padroes.yaml)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

PACK_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PACK_ROOT / "rules" / "catalog.yaml"
PADROES_PATH = PACK_ROOT / "rules" / "padroes.yaml"

TIPOS = ("estatico", "semi", "semantico")
SEVERIDADES = ("CRITICO", "IMPORTANTE", "MELHORIA")
STATUS_ATIVO = "ativo"


def _load_yaml_rules(path: Path) -> list[dict[str, Any]]:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("regras") or [])


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    """Retorna a lista de regras do catalogo de metadados."""
    return _load_yaml_rules(path or CATALOG_PATH)


def load_padroes(path: Path | None = None) -> list[dict[str, Any]]:
    """Retorna a lista de regras executaveis pelo motor declarativo."""
    return _load_yaml_rules(path or PADROES_PATH)


def rule_status(regra: dict[str, Any]) -> str:
    """Status efetivo: ausente com `check` equivale a `ativo`."""
    status = str(regra.get("status") or "").strip().lower()
    if status:
        return status
    return STATUS_ATIVO if regra.get("check") else ""


def split_check(regra: dict[str, Any]) -> tuple[str, str]:
    """`rules/padroes.yaml#EV-X` -> (`rules/padroes.yaml`, `EV-X`); sem `#`, ancora vazia."""
    raw = str(regra.get("check") or "")
    arquivo, _, ancora = raw.partition("#")
    return arquivo, ancora


def check_path(regra: dict[str, Any], pack_root: Path | None = None) -> Path | None:
    """Caminho absoluto do arquivo de check da regra, se declarado."""
    arquivo, _ = split_check(regra)
    if not arquivo:
        return None
    return (pack_root or PACK_ROOT) / arquivo


def check_exists(regra: dict[str, Any], pack_root: Path | None = None) -> bool:
    """Arquivo existe e, com ancora, o id existe ativo nesse catalogo do motor."""
    path = check_path(regra, pack_root)
    if path is None or not path.is_file():
        return False
    _, ancora = split_check(regra)
    if not ancora:
        return True
    return any(r.get("id") == ancora and r.get("ativa", True) for r in _load_yaml_rules(path))


def active_static_rules(regras: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Regras `estatico` com check ativo, na ordem do catalogo."""
    return [
        r
        for r in regras
        if r.get("tipo") == "estatico" and r.get("check") and rule_status(r) == STATUS_ATIVO
    ]
