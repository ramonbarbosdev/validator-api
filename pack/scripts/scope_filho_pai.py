#!/usr/bin/env python3
"""Detecta diff/atividade que deve acionar checklist aba/filho (mestre-detalhe)."""
from __future__ import annotations

import re


def _blob(paths: list[str], extra: str = "") -> str:
    return " ".join(paths).lower() + " " + extra.lower()


def activity_suggests_aba_filho(text: str) -> bool:
    if not text.strip():
        return False
    t = text.lower()
    if "aba" in t and any(
        w in t for w in ("cliente", "entidade", "cadastro", "filho", "vincul", "superior")
    ):
        return True
    if re.search(r"clientes?\s+superior", t):
        return True
    if "mestre" in t and "detalhe" in t:
        return True
    return False


def diff_suggests_filho_pai(changed_files: list[str]) -> bool:
    b = _blob(changed_files)
    pai_hints = (
        "entidade",
        "conta-pagar",
        "conta-receber",
        "colaborador",
        "contrato",
    )
    filho_hints = (
        "dependente",
        "superior",
        "pagamento",
        "recebimento",
        "endereco",
        "contato",
        "cnae",
        "subcategoria",
        "dadosbancarios",
        "aditivo",
        "/itens",
        "clientes-superiores",
    )
    if not any(p in b for p in pai_hints):
        return False
    if any(f in b for f in filho_hints):
        return True
    if "controller" in b and re.search(r"\{id\}/", b):
        return True
    return False


def should_apply_filho_pai_checklist(
    changed_files: list[str],
    *,
    pr_body: str = "",
    pr_discussion: str = "",
) -> bool:
    extra = f"{pr_body}\n{pr_discussion}"
    if activity_suggests_aba_filho(extra):
        return True
    return diff_suggests_filho_pai(changed_files)


def filho_pai_prompt_block() -> str:
    return """
**Checklist obrigatorio (aba/filho no cadastro):** leia `docs/validador/processo/checklist-aba-filho-pai.md` e regras `EV-MD-*` (`.cursor/rules/ev-mestre-detalhe.mdc`).
Compare com vizinho do mesmo pai (ex.: Entidade: enderecos/contatos no `EntidadeRequest` + `EntidadeService`) e com mestre-detalhe financeiro (`mestre-detalhe-conta-receber.md`).
Verifique: escrita no POST/PUT do pai vs sub-rota isolada; POST sem id do pai; GET mestre vs GET da aba; deletar pai e FK do vinculo.
Controller: GET/POST/PUT da aba no **mesmo** controller do pai (`EV-MD-004`), salvo justificativa na SPEC/atividade/comentarios humanos na PR — nesse caso validar o combinado, nao reprovar por vizinho generico.
O CI analisa o repo (`filho_pai_analyze.py`): pares `PaiController` + `Pai*Filho*Controller` com @RestController, sub-rotas `/{id}/…` e gaps de agregado. Nao marque [x] se os fatos automaticos contradizerem o codigo.
"""
