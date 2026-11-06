#!/usr/bin/env python3
"""Mescla achados estaticos (findings-estaticos.json) no relatorio do agente e recalcula a Conclusao."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from report_quality import norm, section_has_findings  # noqa: E402

SECOES = {
    "CRITICO": ("critico", "## Critico"),
    "IMPORTANTE": ("importante", "## Importante"),
    "MELHORIA": ("melhoria", "## Melhoria / Ajuste"),
}
ORDEM_SECOES = ("review", "critico", "importante", "melhoria", "conferencia", "conclusao")
_HEADING = re.compile(r"(?m)^##[ \t]+(.+?)[ \t]*$")
_ITEM = re.compile(r"(?m)^[*-][ \t]+")
_NENHUM = re.compile(r"^\s*nenhum\.?\s*$", re.I)


def _marker(achado: dict[str, Any]) -> str:
    return f"<!-- estatico {achado.get('id')} {achado.get('arquivo')}:{achado.get('linha')} -->"


def _section_key(title: str) -> str:
    t = norm(title)
    for key in ORDEM_SECOES:
        if t.startswith(key) or (key == "melhoria" and "melhoria" in t):
            return key
    return t


def _split(report: str) -> tuple[str, list[list[str]]]:
    """(preambulo, [[titulo, linha_do_titulo, corpo], ...])."""
    matches = list(_HEADING.finditer(report))
    if not matches:
        return report, []
    preambulo = report[: matches[0].start()]
    blocos = []
    for i, m in enumerate(matches):
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(report)
        blocos.append([m.group(1), m.group(0), report[m.end():fim]])
    return preambulo, blocos


def _join(preambulo: str, blocos: list[list[str]]) -> str:
    return preambulo + "".join(linha + corpo for _, linha, corpo in blocos)


def _items(corpo: str) -> list[str]:
    starts = [m.start() for m in _ITEM.finditer(corpo)]
    return [corpo[s: (starts[i + 1] if i + 1 < len(starts) else len(corpo))] for i, s in enumerate(starts)]


def _already_reported(achado: dict[str, Any], corpos: list[str]) -> bool:
    """Mesmo id + arquivo (ou nome do arquivo) + linha no mesmo item, ou marcador do merge."""
    marker = _marker(achado)
    rid = str(achado.get("id") or "")
    arquivo = str(achado.get("arquivo") or "")
    nomes = {arquivo, Path(arquivo).name} - {""}
    linha = str(achado.get("linha") or "")
    for corpo in corpos:
        if marker in corpo:
            return True
        for item in _items(corpo):
            if rid in item and any(n in item for n in nomes) and re.search(rf"(?<!\d){re.escape(linha)}(?!\d)", item):
                return True
    return False


def format_finding(achado: dict[str, Any]) -> str:
    """Achado no formato dos itens do relatorio (titulo + Onde/Problema/Impacto/Correcao)."""
    rid = achado.get("id")
    local = f"{achado.get('arquivo')}:{achado.get('linha')}"
    return (
        f"* **{rid}: {achado.get('evidencia')}** {_marker(achado)}\n\n"
        f"  * **Onde:** `{local}`\n"
        f"  * **Problema:** {achado.get('evidencia')} (regra {rid}, verificada por script).\n"
        f"  * **Impacto:** codigo novo fora da padronizacao do projeto ({rid}).\n"
        f"  * **Correção:** {achado.get('como_corrigir') or 'Ajustar ao padrao da regra.'}\n"
    )


def _insert(corpo: str, texto: str) -> str:
    if not corpo.strip() or _NENHUM.match(corpo):
        return f"\n\n{texto}\n\n"
    return corpo.rstrip("\n") + f"\n\n{texto}\n\n"


def _ensure_section(blocos: list[list[str]], key: str, heading: str) -> list[str]:
    for b in blocos:
        if _section_key(b[0]) == key:
            return b
    novo = [heading[3:], heading, "\n\nNenhum.\n\n"]
    alvo = ORDEM_SECOES.index(key)
    pos = len(blocos)
    for i, b in enumerate(blocos):
        k = _section_key(b[0])
        if k in ORDEM_SECOES and ORDEM_SECOES.index(k) > alvo:
            pos = i
            break
    if pos > 0 and not blocos[pos - 1][2].endswith("\n\n"):
        blocos[pos - 1][2] = blocos[pos - 1][2].rstrip("\n") + "\n\n"
    blocos.insert(pos, novo)
    return novo


def _achados(findings: Any) -> list[dict[str, Any]]:
    if isinstance(findings, dict):
        findings = findings.get("achados") or []
    return [a for a in (findings or []) if isinstance(a, dict) and a.get("id")]


def compute_verdict(report: str) -> str:
    """`NAO APROVAVEL` se Critico ou Importante tem item alem de `Nenhum.`; senao `APROVAVEL`."""
    _, blocos = _split(report)
    for titulo, _, corpo in blocos:
        if _section_key(titulo) in ("critico", "importante") and section_has_findings(corpo):
            return "NAO APROVAVEL"
    return "APROVAVEL"


def _set_conclusion(report: str) -> str:
    linha = f"Conclusao: {compute_verdict(report)}"
    preambulo, blocos = _split(report)
    for b in blocos:
        if _section_key(b[0]) == "conclusao":
            b[2] = f"\n\n{linha}\n"
            return _join(preambulo, blocos)
    return report.rstrip("\n") + f"\n\n## Conclusao\n\n{linha}\n"


def merge(report_md: str, findings: Any) -> str:
    """Insere achados estaticos ausentes na secao da severidade e recalcula `Conclusao:` (idempotente)."""
    preambulo, blocos = _split(report_md)
    for achado in _achados(findings):
        sev = str(achado.get("severidade") or "").upper()
        if sev not in SECOES:
            continue
        corpos = [b[2] for b in blocos]
        if _already_reported(achado, corpos):
            continue
        key, heading = SECOES[sev]
        bloco = _ensure_section(blocos, key, heading)
        bloco[2] = _insert(bloco[2], format_finding(achado).rstrip("\n"))
    return _set_conclusion(_join(preambulo, blocos))
