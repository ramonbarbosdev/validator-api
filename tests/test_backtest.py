"""Backtest offline: tabela por regra/intervalo, sem alterar o checkout nem deixar refs."""
from __future__ import annotations

import json

import pytest

import backtest

SERVICE = "src/main/java/com/esimples_api/service/BancoService.java"
JAVA = "package x;\n\n/** B. */\npublic class BancoService {\n\n    public void salvar() {\n        // grava\n    }\n}\n"
SQL = "CREATE TABLE banco (\n    id_banco BIGSERIAL PRIMARY KEY,\n    nome VARCHAR(10)\n);\n"


@pytest.fixture
def historico(git_repo):
    base = git_repo.git("rev-parse", "HEAD").strip()
    git_repo.write(SERVICE, JAVA)
    meio = git_repo.commit("service")
    git_repo.write("src/main/resources/db/migration/V1__banco.sql", SQL)
    topo = git_repo.commit("migration")
    return git_repo, base, meio, topo


def test_parse_range():
    assert backtest.parse_range("a..b") == ("a", "b")
    assert backtest.parse_range("a...b") == ("a", "b")
    with pytest.raises(ValueError):
        backtest.parse_range("a")


def test_backtest_conta_por_regra_e_limpa(historico, tmp_path, capsys):
    repo, base, meio, topo = historico
    saida = tmp_path / "out.json"
    assert backtest.main(["--repo", str(repo.path), "--range", f"{base}..{meio}",
                          "--range", f"{meio}..{topo}", "--json", str(saida)]) == 0

    tabela = capsys.readouterr().out
    linhas = {ln.split(" | ")[0].strip("| "): ln for ln in tabela.splitlines() if ln.startswith("| EV-")}
    assert linhas["EV-COM-001"].endswith("| 1 | 0 | 1 |")
    assert linhas["EV-SVC-002"].endswith("| 1 | 0 | 1 |")
    assert linhas["EV-DDL-002"].endswith("| 0 | 1 | 1 |")

    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert [d["intervalo"] for d in dados] == [f"{base}..{meio}", f"{meio}..{topo}"]

    assert backtest.BACKTEST_REF not in repo.git("for-each-ref")
    assert repo.git("worktree", "list").count("\n") == 1
    assert repo.git("status", "--porcelain") == ""
