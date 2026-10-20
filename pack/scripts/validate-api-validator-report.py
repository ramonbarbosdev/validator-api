#!/usr/bin/env python3
"""Gate de qualidade do relatorio antes de publicar na PR."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from report_public import write_public_report


def norm(text: str) -> str:
    """ASCII minusculo sem acentos (Conclusao == Conclusão)."""
    folded = unicodedata.normalize("NFKD", text)
    return folded.encode("ascii", "ignore").decode().lower()


def file_mentioned_in_report(name: str, body: str) -> bool:
    """Caminho completo, nome do arquivo ou stem da classe no relatorio."""
    if name in body:
        return True
    base = Path(name).name
    if base in body:
        return True
    stem = Path(name).stem
    if len(stem) >= 4 and re.search(rf"\b{re.escape(stem)}\b", body):
        return True
    return False


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


def parse_conclusion_verdict(body: str) -> str | None:
    """Retorna 'nao aprovavel' | 'aprovavel com ressalvas' | 'aprovavel' (normalizado)."""
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


def _report_sections(body: str) -> dict[str, str]:
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


def check_conclusion_matches_findings(body: str) -> str | None:
    sections = _report_sections(body)
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
            mentioned = any(
                file_mentioned_in_report(name, body) for name in changed[:40]
            )
            if not mentioned:
                errors.append(
                    "Relatorio nao cita nenhum arquivo do diff "
                    f"(ex.: {changed[0]}). Revisao provavelmente superficial."
                )

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
