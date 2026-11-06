"""Catalogo de regras: carga, IDs unicos, checks existentes e cobertura das fontes."""
from __future__ import annotations

import re

from conftest import PACK
from rules_catalog import (
    SEVERIDADES,
    TIPOS,
    active_static_rules,
    check_path,
    load_catalog,
    rule_status,
)


def _fontes_ev_ids() -> set[str]:
    fontes = list((PACK / ".cursor" / "rules").glob("*.mdc"))
    fontes.append(PACK / ".cursor" / "agents" / "api-validator.md")
    ids: set[str] = set()
    for f in fontes:
        ids.update(re.findall(r"EV-[A-Z]+-\d{3}", f.read_text(encoding="utf-8")))
    return ids


def test_catalogo_carrega_com_campos_validos():
    regras = load_catalog()
    assert regras
    for r in regras:
        assert r.get("id"), r
        assert r.get("severidade") in SEVERIDADES, r["id"]
        assert r.get("tipo") in TIPOS, r["id"]
        assert r.get("descricao"), r["id"]


def test_catalogo_sem_ids_duplicados():
    ids = [r["id"] for r in load_catalog()]
    assert len(ids) == len(set(ids)), sorted(i for i in ids if ids.count(i) > 1)


def test_check_ativo_aponta_para_arquivo_real():
    for r in load_catalog():
        if r.get("check") and rule_status(r) == "ativo":
            assert check_path(r).is_file(), f"{r['id']}: {r['check']}"


def test_estatico_sem_script_marcado_pendente():
    for r in load_catalog():
        if r.get("tipo") != "estatico" or rule_status(r) == "substituida":
            continue
        assert r.get("check"), r["id"]
        if not check_path(r).is_file():
            assert rule_status(r) == "pendente", r["id"]


def test_ev_svc_003_substituida_por_ev_com_001():
    regra = next(r for r in load_catalog() if r["id"] == "EV-SVC-003")
    assert regra.get("substituida_por") == "EV-COM-001"


def test_todas_as_regras_das_fontes_estao_no_catalogo():
    faltando = _fontes_ev_ids() - {r["id"] for r in load_catalog()}
    assert not faltando, sorted(faltando)


def test_regras_estaticas_ativas():
    ids = [r["id"] for r in active_static_rules(load_catalog())]
    assert ids == ["EV-COM-001", "EV-DDL-002"]
