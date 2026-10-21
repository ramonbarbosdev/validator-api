#!/usr/bin/env python3
"""Gate: relatorio vs analise generica mestre-filho (filho_pai_analyze)."""
from __future__ import annotations

import os
from pathlib import Path

from filho_pai_analyze import analyze_repo
from report_quality import norm, report_sections, section_has_findings


def _enabled() -> bool:
    raw = os.environ.get("CURSOR_VALIDATOR_VERIFY_FILHO_PAI_CODE", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _justification_allows_child_controller(text: str, controller_paths: list[str]) -> bool:
    if not text.strip():
        return False
    n = norm(text)
    if "ev-md-004" in n and any(w in n for w in ("manter", "legado", "justific", "excecao", "permissao")):
        return True
    for path in controller_paths:
        stem = Path(path).stem.lower()
        if stem in n and any(w in n for w in ("manter", "legado", "justific", "excecao", "nao remover")):
            return True
    return False


def load_scope_justification(repo_root: Path, pr_number: str | None) -> str:
    parts: list[str] = []
    for key in ("GITHUB_PR_BODY", "CURSOR_VALIDATOR_JUSTIFICATION"):
        val = os.environ.get(key, "").strip()
        if val:
            parts.append(val)
    if pr_number and pr_number.isdigit():
        review_dir = repo_root / ".api-validator-review"
        for name in (f"pr-{pr_number}-discussion.md", f"pr-{pr_number}-previous-report.md"):
            p = review_dir / name
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _report_claims_clean(report_body: str) -> bool:
    sections = report_sections(report_body)
    if section_has_findings(sections.get("critico", "")):
        return False
    if section_has_findings(sections.get("importante", "")):
        return False
    return True


def _checklist_cites_child_as_fixed(report_body: str, child_class_names: list[str]) -> bool:
    if "[x]" not in report_body:
        return False
    nbody = norm(report_body)
    for name in child_class_names:
        if norm(name) in nbody:
            return True
    return False


def verify_report_vs_code(
    repo_root: Path,
    report_body: str,
    *,
    pr_number: str | None = None,
) -> list[str]:
    if not _enabled():
        return []
    analysis = analyze_repo(repo_root)
    controllers = analysis.child_rel_paths()
    if not controllers:
        return []

    justification = load_scope_justification(repo_root, pr_number)
    if _justification_allows_child_controller(justification, controllers):
        return []

    child_names = [p.child_class for p in analysis.dedicated_children]
    listed = ", ".join(controllers)
    errors: list[str] = []

    if _checklist_cites_child_as_fixed(report_body, child_names) and _report_claims_clean(report_body):
        errors.append(
            "Relatorio marca checklist [x] citando controller do filho, mas o @RestController dedicado "
            f"ainda existe ({listed}). Remover/mover para o controller do pai ou achado EV-MD-004 em Importante."
        )
    elif _report_claims_clean(report_body):
        pairs = "; ".join(f"{p.child_class}→{p.parent_class}" for p in analysis.dedicated_children[:5])
        errors.append(
            f"Padrao mestre-filho: controller dedicado do filho detectado ({listed}) — EV-MD-004 ({pairs}). "
            "Importante/Critico nao podem ser so 'Nenhum.' sem justificativa na SPEC/PR."
        )
    return errors
