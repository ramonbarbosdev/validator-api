"""Decisao de label de bloqueio (reutiliza gate do pacote em pack/scripts)."""
from __future__ import annotations

import sys
from pathlib import Path


def _pack_scripts(validator_root: Path) -> None:
    scripts = validator_root / "scripts"
    if scripts.is_dir():
        p = str(scripts)
        if p not in sys.path:
            sys.path.insert(0, p)


def _with_static_findings(report_text: str, repo_root: Path) -> str:
    """Mescla findings-estaticos.json (se a flag estiver ligada); qualquer erro devolve o texto original."""
    try:
        from merge_static_findings import merge
        from run_static_checks import load_findings, static_checks_enabled
    except ImportError:
        return report_text
    if not static_checks_enabled():
        return report_text
    findings = load_findings(repo_root)
    if findings is None:
        return report_text
    try:
        return merge(report_text, findings)
    except Exception:
        return report_text


def needs_block_label(
    report_text: str,
    repo_root: Path,
    validator_root: Path,
    *,
    pr_number: int | None = None,
    gate_failed: bool = False,
) -> bool:
    """True -> aplicar API_VALIDATOR_BLOCK_LABEL na PR."""
    if gate_failed:
        return True

    _pack_scripts(validator_root)
    try:
        from report_quality import parse_conclusion_verdict, report_sections, section_has_findings
        from verify_filho_pai_code import verify_report_vs_code
    except ImportError:
        from validator_api.github import parse_report_verdict

        return parse_report_verdict(report_text) != "aprovavel"

    report_text = _with_static_findings(report_text, repo_root)

    sections = report_sections(report_text)
    if section_has_findings(sections.get("critico", "")):
        return True
    if section_has_findings(sections.get("importante", "")):
        return True

    verdict = parse_conclusion_verdict(report_text)
    if verdict != "aprovavel":
        return True

    pr_key: str | None = str(pr_number) if pr_number is not None else None
    code_errors = verify_report_vs_code(repo_root, report_text, pr_number=pr_key)
    if code_errors:
        return True

    return False
