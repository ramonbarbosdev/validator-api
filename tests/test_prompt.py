"""Prompt do agente: snapshot legado com checks desligados e bloco de achados estaticos."""
from __future__ import annotations

import pytest

from _ci_module import SNAPSHOT, build_default_prompt, load_ci_module, prompt_kwargs


@pytest.fixture
def ci(monkeypatch):
    monkeypatch.delenv("VALIDATOR_REPO", raising=False)
    monkeypatch.delenv("VALIDATOR_PIN_SHA", raising=False)
    return load_ci_module()


def _prompt(ci, static_findings):
    kwargs = prompt_kwargs()
    return ci.build_prompt(
        kwargs.pop("root"), kwargs.pop("base"), kwargs.pop("pr_label"),
        kwargs.pop("stat"), kwargs.pop("spec_line"), static_findings=static_findings, **kwargs,
    )


RESULTADO = {
    "achados": [
        {"id": "EV-COM-001", "severidade": "IMPORTANTE", "arquivo": "src/A.java", "linha": 7,
         "evidencia": "comentario de linha (//): // x", "como_corrigir": "Remova o comentario."},
    ],
    "falhas_de_regra": [{"id": "EV-NOM-001", "erro": "boom"}],
    "regras_executadas": ["EV-COM-001", "EV-DDL-002", "EV-SVC-002"],
    "regras_inativas": [],
    "regras_llm_aplicaveis": [{"id": "EV-REU-001", "severidade": "IMPORTANTE", "descricao": "Reutilizar."}],
}


def test_prompt_sem_checks_identico_ao_legado(ci):
    esperado = SNAPSHOT.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert build_default_prompt(ci) == esperado
    assert _prompt(ci, None) == esperado


def test_main_com_flag_desligada_nao_roda_checks(ci, monkeypatch):
    monkeypatch.setenv("VALIDATOR_STATIC_CHECKS", "0")
    assert not ci.static_checks_enabled()


def test_prompt_com_checks_injeta_bloco_e_troca_regra_de_comentario(ci):
    texto = _prompt(ci, RESULTADO)
    assert ci.STATIC_BLOCK_TITLE in texto
    assert "- **EV-COM-001** (IMPORTANTE) `src/A.java:7` — comentario de linha (//): // x" in texto
    assert "EV-NOM-001): avalie manualmente" in texto
    assert "- **EV-REU-001**: Reutilizar." in texto
    assert ci.LEGACY_COMMENT_RULE not in texto
    assert "sao verificados por script" in texto


def test_prompt_com_motor_indisponivel_mantem_regra_legada(ci):
    falhou = {"achados": [], "falhas_de_regra": [{"id": "motor", "erro": "ImportError"}],
              "regras_executadas": [], "regras_llm_aplicaveis": []}
    texto = _prompt(ci, falhou)
    assert ci.LEGACY_COMMENT_RULE in texto
    assert "Nenhum achado estatico" in texto
