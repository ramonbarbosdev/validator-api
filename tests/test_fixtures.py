"""Cada regra estatica ativa tem `fixtures/<ID>/ruim` (deve disparar) e `fixtures/<ID>/bom` (nao deve)."""
from __future__ import annotations

from pathlib import Path

import pytest

import run_static_checks as rsc
from rules_catalog import active_static_rules, load_catalog

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CASOS = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir())


def _aplicar(novo_repo, pasta: Path) -> Path:
    arquivos = {
        f.relative_to(pasta).as_posix(): f.read_text(encoding="utf-8")
        for f in pasta.rglob("*") if f.is_file()
    }
    return novo_repo(arquivos)


def _achados(novo_repo, regra: str, variante: str) -> list[dict]:
    resultado = rsc.run_static_checks("develop", _aplicar(novo_repo, FIXTURES / regra / variante))
    assert resultado["falhas_de_regra"] == []
    return [a for a in resultado["achados"] if a["id"] == regra]


def test_toda_regra_estatica_ativa_tem_fixture():
    ativas = {r["id"] for r in active_static_rules(load_catalog())}
    assert ativas <= set(CASOS)


@pytest.mark.parametrize("regra", CASOS)
def test_fixture_ruim_dispara(novo_repo, regra):
    assert _achados(novo_repo, regra, "ruim"), f"{regra}/ruim nao gerou achado"


@pytest.mark.parametrize("regra", CASOS)
def test_fixture_bom_nao_dispara(novo_repo, regra):
    assert _achados(novo_repo, regra, "bom") == []
