"""Catalogo de regras: carga, IDs unicos, checks existentes e cobertura das fontes."""
from __future__ import annotations

import re

from conftest import PACK
from rules_catalog import (
    SEVERIDADES,
    TIPOS,
    active_static_rules,
    check_exists,
    load_catalog,
    load_padroes,
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
            assert check_exists(r), f"{r['id']}: {r['check']}"


def test_estatico_sem_regra_no_motor_marcado_pendente():
    for r in load_catalog():
        if r.get("tipo") != "estatico" or rule_status(r) == "substituida":
            continue
        assert r.get("check"), r["id"]
        if not check_exists(r):
            assert rule_status(r) == "pendente", r["id"]


def test_substituicoes():
    por_id = {r["id"]: r for r in load_catalog()}
    assert por_id["EV-SVC-003"].get("substituida_por") == "EV-COM-001"
    assert por_id["EV-TXN-003"].get("substituida_por") == "EV-CTL-004"


def test_todas_as_regras_das_fontes_estao_no_catalogo():
    faltando = _fontes_ev_ids() - {r["id"] for r in load_catalog()}
    assert not faltando, sorted(faltando)


def test_regras_estaticas_do_motor_estao_no_catalogo_com_mesma_severidade():
    catalogo = {r["id"]: r for r in load_catalog()}
    for p in load_padroes():
        if p.get("tipo") == "llm" or not p.get("ativa", True):
            continue
        assert p["id"] in catalogo, p["id"]
        assert catalogo[p["id"]]["severidade"] == p["severidade"], p["id"]
        assert catalogo[p["id"]].get("check") == f"rules/padroes.yaml#{p['id']}", p["id"]


def test_regras_estaticas_ativas():
    ids = sorted(r["id"] for r in active_static_rules(load_catalog()))
    assert ids == sorted(
        ["EV-COM-001", "EV-DDL-002", "EV-DDL-003", "EV-SVC-002", "EV-CTL-002",
         "EV-CTL-004", "EV-NOM-001", "EV-PER-004", "EV-REST-002"]
    )
