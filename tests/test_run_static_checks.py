"""Wrapper do motor: achados reais, robustez a falhas e flag VALIDATOR_STATIC_CHECKS."""
from __future__ import annotations

import json

import run_static_checks as rsc

JAVA_COM_COMENTARIO = """package com.esimples_api.service;

/**
 * Banco.
 */
public class BancoService {

    /** Salva. */
    public void salvar() {
        // grava o banco
        int x = 1;
    }
}
"""

SQL_COLUNA_RUIM = """CREATE TABLE banco (
    id_banco BIGSERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    dt_criacao TIMESTAMP,
    nu_documento VARCHAR(20)
);
"""

SERVICE = "src/main/java/com/esimples_api/service/BancoService.java"
MIGRATION = "src/main/resources/db/migration/V10__banco.sql"


def _pr(novo_repo):
    return novo_repo({SERVICE: JAVA_COM_COMENTARIO, MIGRATION: SQL_COLUNA_RUIM})


def test_runner_encontra_comentario_e_coluna(novo_repo):
    resultado = rsc.run_static_checks("develop", _pr(novo_repo))
    assert resultado["falhas_de_regra"] == []
    achados = sorted((a["id"], a["arquivo"], a["linha"]) for a in resultado["achados"])
    assert achados == [("EV-COM-001", SERVICE, 10), ("EV-DDL-002", MIGRATION, 3)]
    assert "EV-COM-001" in resultado["regras_executadas"]


def test_executar_com_excecao_nao_derruba(novo_repo, monkeypatch):
    repo = _pr(novo_repo)
    motor = rsc._motor()

    def quebra(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(motor, "executar", quebra)
    resultado = rsc.run_static_checks("develop", repo)
    assert resultado["achados"] == []
    assert resultado["falhas_de_regra"][0]["id"] == "motor"
    assert "boom" in resultado["falhas_de_regra"][0]["erro"]


def test_catalogo_invalido_registra_falha(novo_repo, tmp_path):
    repo = _pr(novo_repo)
    regras = tmp_path / "padroes.yaml"
    regras.write_text("regras:\n  - {id: X, tipo: xyz, severidade: IMPORTANTE}\n", encoding="utf-8")
    resultado = rsc.run_static_checks("develop", repo, regras_path=regras)
    assert resultado["falhas_de_regra"][0]["id"] == "catalogo"


def test_regra_quebrada_nao_derruba_as_outras(novo_repo, tmp_path):
    repo = _pr(novo_repo)
    regras = tmp_path / "padroes.yaml"
    regras.write_text(
        "regras:\n"
        "  - {id: Q, tipo: par_obrigatorio, severidade: IMPORTANTE, origem: '(.*)', destino: '\\9'}\n"
        "  - {id: EV-COM-001, tipo: comentarios, severidade: IMPORTANTE}\n",
        encoding="utf-8",
    )
    resultado = rsc.run_static_checks("develop", repo, regras_path=regras)
    assert [f["id"] for f in resultado["falhas_de_regra"]] == ["Q"]
    assert [a["id"] for a in resultado["achados"]] == ["EV-COM-001"]


def test_repo_sem_git_registra_falha(tmp_path):
    resultado = rsc.run_static_checks("develop", tmp_path)
    assert resultado["achados"] == []
    assert resultado["falhas_de_regra"][0]["id"] == "motor"


def test_cli_grava_json_e_sai_zero(novo_repo, tmp_path):
    repo = _pr(novo_repo)
    saida = tmp_path / "saida"
    assert rsc.main(["develop", str(repo), str(saida)]) == 0
    data = json.loads((saida / rsc.FINDINGS_NAME).read_text(encoding="utf-8"))
    assert {"achados", "falhas_de_regra", "regras_executadas", "regras_llm_aplicaveis"} <= set(data)
    assert rsc.load_findings(saida) == data


def test_load_findings_invalido(tmp_path):
    assert rsc.load_findings(tmp_path) is None
    (tmp_path / rsc.FINDINGS_NAME).write_text("{quebrado", encoding="utf-8")
    assert rsc.load_findings(tmp_path) is None


def test_flag_static_checks(monkeypatch):
    monkeypatch.delenv(rsc.ENV_FLAG, raising=False)
    assert rsc.static_checks_enabled()
    for valor in ("0", "false", "no", "off"):
        monkeypatch.setenv(rsc.ENV_FLAG, valor)
        assert not rsc.static_checks_enabled()
    monkeypatch.setenv(rsc.ENV_FLAG, "1")
    assert rsc.static_checks_enabled()
