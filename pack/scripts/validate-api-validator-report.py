#!/usr/bin/env python3
"""Gate de qualidade do relatorio antes de publicar na PR."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from report_public import write_public_report
from report_quality import (
    has_previous_round_checklist,
    mentions_any_changed_file,
    norm,
    parse_conclusion_verdict,
    previous_report_had_findings,
    report_sections,
    section_has_findings,
)
from verify_filho_pai_code import verify_report_vs_code  # noqa: E402


def git_diff_names(root: Path, base: str) -> list[str]:
    for ref in (f"origin/{base}...HEAD", f"origin/{base}", "HEAD"):
        try:
            out = subprocess.check_output(
                ["git", "diff", "--name-only", ref],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            names = [ln.strip() for ln in out.splitlines() if ln.strip()]
            if names:
                return names
        except subprocess.CalledProcessError:
            continue
    return []


def has_section(body: str, *keywords: str) -> bool:
    nbody = norm(body)
    for kw in keywords:
        nk = norm(kw)
        if nk in nbody:
            return True
        if re.search(rf"(?m)^#+\s*{re.escape(nk)}\b", nbody):
            return True
        if re.search(rf"\*\*{re.escape(nk)}\*\*", nbody):
            return True
    return False


def has_conclusion_verdict(body: str) -> bool:
    return parse_conclusion_verdict(body) is not None


def check_conclusion_matches_findings(body: str) -> str | None:
    sections = report_sections(body)
    critico = sections.get("critico", "")
    importante = sections.get("importante", "")
    has_crit = section_has_findings(critico)
    has_imp = section_has_findings(importante)
    verdict = parse_conclusion_verdict(body)

    if has_crit or has_imp:
        if verdict != "nao aprovavel":
            return (
                "Com itens em Critico ou Importante, conclusao deve ser "
                "NAO APROVAVEL (nao APROVAVEL nem APROVAVEL COM RESSALVAS)."
            )
        return None

    if verdict != "aprovavel":
        return (
            "Sem itens em Critico e Importante (Nenhum.), conclusao deve ser APROVAVEL."
        )
    return None


def main() -> int:
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    report = root / "api-validator-report.md"
    if not report.is_file():
        print(f"Falta {report}", file=sys.stderr)
        return 1

    text = report.read_text(encoding="utf-8")
    body = text
    for heading in ("## Review", "## API Validator", "## Código Review"):
        if heading in text:
            body = text.split(heading, 1)[-1]
            break

    errors: list[str] = []

    if not has_section(body, "Critico", "Crítico"):
        # Aceita achado explicito sem titulo (legado do prompt sem acento)
        if not re.search(r"(?i)crit[ií]co\s*:", body) and "nenhum" not in norm(body):
            errors.append("Secao ausente: Critico (ou linha Critico: / Nenhum.)")

    if not has_section(body, "Importante"):
        errors.append("Secao ausente: Importante")

    if not has_section(body, "Melhoria", "Ajuste"):
        errors.append("Secao ausente: Melhoria / Ajuste")

    if not has_section(body, "Conclusao", "Conclusão") and not has_conclusion_verdict(
        body
    ):
        errors.append("Secao ausente: Conclusao (ou linha Conclusao: APROVAVEL ...)")

    if len(body.strip()) < 280:
        errors.append("Relatorio muito curto (possivel resposta generica).")

    if not has_conclusion_verdict(body):
        errors.append(
            "Conclusao invalida ou ausente (esperado: NAO APROVAVEL ou APROVAVEL)."
        )
    else:
        mismatch = check_conclusion_matches_findings(body)
        if mismatch:
            errors.append(mismatch)

    strict = os.environ.get("CURSOR_VALIDATOR_STRICT_REPORT", "1").strip() not in (
        "0",
        "false",
        "no",
    )
    if strict:
        base = os.environ.get("GITHUB_BASE_REF", "develop").removeprefix("origin/")
        changed = git_diff_names(root, base)
        if changed:
            if not mentions_any_changed_file(body, changed):
                errors.append(
                    "Relatorio nao cita nenhum arquivo do diff "
                    f"(ex.: {changed[0]}). Revisao provavelmente superficial."
                )

    pr_raw = os.environ.get("PR_NUMBER", "").strip()
    prev_path = None
    if pr_raw.isdigit():
        prev_path = root / ".api-validator-review" / f"pr-{pr_raw}-previous-report.md"
    prev_md = prev_path.read_text(encoding="utf-8") if prev_path and prev_path.is_file() else ""
    if previous_report_had_findings(prev_md):
        sections = report_sections(body)
        if not section_has_findings(sections.get("critico", "")) and not section_has_findings(
            sections.get("importante", "")
        ):
            if not has_previous_round_checklist(body):
                errors.append(
                    "Havia pendencias no relatorio anterior: inclua "
                    "## Conferencia da rodada anterior com checklist - [x] por ponto fechado "
                    "(ou achados abertos em Critico/Importante)."
                )

    pr_num = pr_raw if pr_raw.isdigit() else None
    errors.extend(verify_report_vs_code(root, body, pr_number=pr_num))

    if errors:
        print("Relatorio reprovado no gate de qualidade:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    write_public_report(root)
    print("Relatorio ok (gate de qualidade).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
