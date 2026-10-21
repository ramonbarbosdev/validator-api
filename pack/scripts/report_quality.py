#!/usr/bin/env python3
"""Checagens compartilhadas do relatorio api-validator."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def norm(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    return folded.encode("ascii", "ignore").decode().lower()


def file_mentioned_in_report(name: str, body: str) -> bool:
    if name in body:
        return True
    base = Path(name).name
    if base in body:
        return True
    stem = Path(name).stem
    if len(stem) >= 4 and re.search(rf"\b{re.escape(stem)}\b", body):
        return True
    return False


def parse_conclusion_verdict(body: str) -> str | None:
    nbody = norm(body)
    m = re.search(
        r"conclus[aã]o\s*:?\s*"
        r"(nao\s+aprov[aá]vel|aprov[aá]vel\s+com\s+ressalvas|aprov[aá]vel)\b",
        nbody,
    )
    if m:
        return m.group(1)
    m2 = re.search(
        r"(?m)^##\s*conclus[aã]o\s*\n\s*"
        r"(nao\s+aprov[aá]vel|aprov[aá]vel\s+com\s+ressalvas|aprov[aá]vel)\s*$",
        nbody,
    )
    if m2:
        return m2.group(1)
    return None


def report_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    chunks = re.split(r"(?m)^##\s+", body)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        title_line, _, rest = chunk.partition("\n")
        sections[norm(title_line.strip())] = rest
    return sections


def section_has_findings(section_body: str) -> bool:
    t = section_body.strip()
    if not t:
        return False
    compact = re.sub(r"\s+", " ", norm(t)).strip()
    if re.fullmatch(r"nenhum\.?", compact):
        return False
    if compact.startswith("nenhum.") and len(compact) < 24:
        return False
    return True


def previous_report_had_findings(previous_markdown: str) -> bool:
    """Relatorio anterior (sidecar/prompt) tinha itens em Critico ou Importante."""
    if not previous_markdown.strip():
        return False
    sections = report_sections(previous_markdown)
    return section_has_findings(sections.get("critico", "")) or section_has_findings(
        sections.get("importante", "")
    )


def mentions_any_changed_file(body: str, changed_files: list[str]) -> bool:
    if not changed_files:
        return True
    return any(file_mentioned_in_report(name, body) for name in changed_files[:40])


def has_previous_round_checklist(body: str) -> bool:
    nbody = norm(body)
    if "conferencia da rodada anterior" not in nbody:
        return False
    return bool(re.search(r"(?m)^-\s*\[[xX ]\]", body))


def agent_output_incomplete(
    body: str,
    changed_files: list[str],
    *,
    had_previous_report: bool = False,
) -> bool:
    """Resposta do agente antes do gate (retry automatico no CI)."""
    text = body.strip()
    if not text:
        return True
    if len(text) < 280:
        return True
    if parse_conclusion_verdict(text) is None:
        return True
    if changed_files and not mentions_any_changed_file(text, changed_files):
        return True
    if had_previous_report and changed_files:
        sections = report_sections(text)
        if not section_has_findings(sections.get("critico", "")) and not section_has_findings(
            sections.get("importante", "")
        ):
            if not has_previous_round_checklist(text):
                return True
    return False
