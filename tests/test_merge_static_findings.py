"""Merge de achados estaticos no relatorio, conclusao calculada e integracao com gate/labels."""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from conftest import PACK
from merge_static_findings import compute_verdict, merge
from report_quality import parse_conclusion_verdict, report_sections, section_has_findings
from validator_api.report_gate import needs_block_label

REPORT_COM_IMPORTANTE = """<!-- review -->
## Review (PR #541)

## Critico

Nenhum.

## Importante

* **Gap de agregado no cadastro**

  * **Onde:** `src/main/java/com/esimples_api/service/EntidadeService.java`
  * **Problema:** Filho salvo fora do POST do pai.
  * **Impacto:** Salvar da tela nao persiste a aba.
  * **Correção:** Persistir o filho no fluxo do pai.

## Melhoria / Ajuste

Nenhum.

## Conferencia da rodada anterior

- [x] **Titulo anterior** — `src/main/java/com/esimples_api/service/A.java` (fecha o ponto)

## Conclusao

Conclusao: NAO APROVAVEL
"""

REPORT_LIMPO = """<!-- review -->
## Review (PR #12)

## Critico

Nenhum.

## Importante

Nenhum.

## Melhoria / Ajuste

Nenhum. Arquivos analisados: `src/main/java/com/esimples_api/service/BancoService.java`, `src/main/resources/db/migration/V10__banco.sql`.

## Conclusao

Conclusao: APROVAVEL
"""

COMENTARIO = {
    "id": "EV-COM-001", "severidade": "IMPORTANTE",
    "arquivo": "src/main/java/com/esimples_api/service/BancoService.java", "linha": 10,
    "evidencia": "comentario de linha (//): // grava o banco",
    "como_corrigir": "Remova o comentario ou passe a informacao para o JavaDoc da declaracao.",
}
CRITICO = {**COMENTARIO, "id": "EV-TST-999", "severidade": "CRITICO", "linha": 3, "evidencia": "x"}
MELHORIA = {**COMENTARIO, "id": "EV-NOM-001", "severidade": "MELHORIA", "linha": 5,
            "evidencia": "url_segmento 'Detalhes' fora do padrao"}


def _secao(texto: str, chave: str) -> str:
    return report_sections(texto)[chave]


def _titulos(texto: str) -> list[str]:
    return [ln for ln in texto.splitlines() if ln.startswith("## ")]


def test_achado_ausente_e_inserido_na_secao_da_severidade():
    out = merge(REPORT_COM_IMPORTANTE, {"achados": [COMENTARIO]})
    importante = _secao(out, "importante")
    assert "Gap de agregado no cadastro" in importante
    assert "**EV-COM-001: comentario de linha (//): // grava o banco**" in importante
    assert f"`{COMENTARIO['arquivo']}:10`" in importante
    assert COMENTARIO["como_corrigir"] in importante
    assert "EV-COM-001" not in _secao(out, "critico")


def test_achado_ja_presente_nao_duplica():
    relatorio = REPORT_COM_IMPORTANTE.replace(
        "* **Gap de agregado no cadastro**",
        "* **Comentario no service (EV-COM-001)**\n\n  * **Onde:** `BancoService.java`, linha 10\n\n"
        "* **Gap de agregado no cadastro**",
    )
    out = merge(relatorio, [COMENTARIO])
    assert out.count("EV-COM-001") == 1


def test_nenhum_e_substituido_pelo_achado():
    out = merge(REPORT_COM_IMPORTANTE, [CRITICO])
    critico = _secao(out, "critico")
    assert "Nenhum." not in critico
    assert "EV-TST-999" in critico


def test_conclusao_muda_para_nao_aprovavel():
    assert parse_conclusion_verdict(REPORT_LIMPO) == "aprovavel"
    out = merge(REPORT_LIMPO, [COMENTARIO])
    assert parse_conclusion_verdict(out) == "nao aprovavel"
    assert _secao(out, "conclusao").strip() == "Conclusao: NAO APROVAVEL"


def test_merge_idempotente():
    uma = merge(REPORT_COM_IMPORTANTE, [COMENTARIO, CRITICO, MELHORIA])
    assert merge(uma, [COMENTARIO, CRITICO, MELHORIA]) == uma
    assert uma.count("<!-- estatico EV-COM-001") == 1


def test_conclusao_errada_do_llm_e_corrigida():
    errado = REPORT_COM_IMPORTANTE.replace("Conclusao: NAO APROVAVEL", "Conclusao: APROVAVEL")
    assert parse_conclusion_verdict(merge(errado, [])) == "nao aprovavel"
    errado_inverso = REPORT_LIMPO.replace("Conclusao: APROVAVEL", "Conclusao: NAO APROVAVEL")
    assert parse_conclusion_verdict(merge(errado_inverso, [])) == "aprovavel"


def test_preserva_conferencia_e_ordem_das_secoes():
    out = merge(REPORT_COM_IMPORTANTE, [COMENTARIO, CRITICO, MELHORIA])
    assert _titulos(out) == _titulos(REPORT_COM_IMPORTANTE)
    assert "- [x] **Titulo anterior**" in _secao(out, "conferencia da rodada anterior")


def test_melhoria_nao_altera_conclusao():
    out = merge(REPORT_LIMPO, [MELHORIA])
    assert "EV-NOM-001" in _secao(out, "melhoria / ajuste")
    assert compute_verdict(out) == "APROVAVEL"


def test_secao_ausente_e_criada_na_ordem():
    sem_critico = REPORT_LIMPO.replace("## Critico\n\nNenhum.\n\n", "")
    out = merge(sem_critico, [CRITICO])
    assert _titulos(out)[:3] == ["## Review (PR #12)", "## Critico", "## Importante"]
    assert section_has_findings(_secao(out, "critico"))


def test_relatorio_sem_conclusao_recebe_secao():
    sem_conclusao = REPORT_LIMPO.split("## Conclusao")[0]
    out = merge(sem_conclusao, [])
    assert _titulos(out)[-1] == "## Conclusao"
    assert parse_conclusion_verdict(out) == "aprovavel"


def test_needs_block_label_com_achado_estatico_mesclado(tmp_path):
    out = merge(REPORT_LIMPO, [COMENTARIO])
    assert needs_block_label(out, tmp_path, PACK) is True
    assert needs_block_label(merge(REPORT_LIMPO, [MELHORIA]), tmp_path, PACK) is False


def test_needs_block_label_le_findings_do_repo(tmp_path, monkeypatch):
    (tmp_path / "findings-estaticos.json").write_text(json.dumps({"achados": [COMENTARIO]}), encoding="utf-8")
    monkeypatch.delenv("VALIDATOR_STATIC_CHECKS", raising=False)
    assert needs_block_label(REPORT_LIMPO, tmp_path, PACK) is True
    monkeypatch.setenv("VALIDATOR_STATIC_CHECKS", "0")
    assert needs_block_label(REPORT_LIMPO, tmp_path, PACK) is False


@pytest.mark.parametrize("flag,esperado_mesclado", [("1", True), ("0", False)])
def test_gate_mescla_relatorio_em_disco(tmp_path, flag, esperado_mesclado):
    (tmp_path / "api-validator-report.md").write_text(REPORT_COM_IMPORTANTE, encoding="utf-8")
    (tmp_path / "findings-estaticos.json").write_text(json.dumps({"achados": [COMENTARIO]}), encoding="utf-8")
    env = {**os.environ, "REPO_ROOT": str(tmp_path), "CURSOR_VALIDATOR_STRICT_REPORT": "0",
           "VALIDATOR_STATIC_CHECKS": flag, "PR_NUMBER": ""}
    proc = subprocess.run(
        [sys.executable, str(PACK / "scripts" / "validate-api-validator-report.py")],
        env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    texto = (tmp_path / "api-validator-report.md").read_text(encoding="utf-8")
    assert ("EV-COM-001" in texto) is esperado_mesclado
    publico = (tmp_path / "api-validator-report-public.md").read_text(encoding="utf-8")
    assert ("EV-COM-001" in publico) is esperado_mesclado
    assert "Conclusao" not in publico
