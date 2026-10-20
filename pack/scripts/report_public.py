#!/usr/bin/env python3
"""Versao publica do relatorio (sem secao Conclusao) para comentario na PR."""
from __future__ import annotations

import re
from pathlib import Path

PUBLIC_NAME = "api-validator-report-public.md"
FULL_NAME = "api-validator-report.md"

_CONCLUSION_HEADING = re.compile(
    r"(?is)\n##\s*Conclus[aã]o\b.*\Z",
)


def strip_conclusion_section(text: str) -> str:
    """Remove bloco ## Conclusao / ## Conclusão até o fim."""
    return _CONCLUSION_HEADING.sub("", text).rstrip() + "\n"


def write_public_report(root: Path) -> Path | None:
    full = root / FULL_NAME
    if not full.is_file():
        return None
    public = root / PUBLIC_NAME
    public.write_text(strip_conclusion_section(full.read_text(encoding="utf-8")), encoding="utf-8")
    return public


if __name__ == "__main__":
    import os
    import sys

    r = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    out = write_public_report(r)
    if not out:
        print(f"Falta {r / FULL_NAME}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Publico: {out}")
