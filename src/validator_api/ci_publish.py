"""Publica relatorio na PR e falha o job se Conclusao: NAO APROVAVEL."""
from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path

from validator_api.github import sync_block_label, upsert_review_comment


def _norm(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    return folded.encode("ascii", "ignore").decode().lower()


def _is_nao_aprovavel(report_text: str) -> bool:
    low = _norm(report_text)
    if re.search(r"conclus[aã]o\s*:\s*nao\s+aprov", low):
        return True
    return "nao aprovavel" in low.replace("ã", "a") and "conclusao" in low


def main() -> int:
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    pr_raw = os.environ.get("PR_NUMBER", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()

    if not repo or not pr_raw.isdigit() or not token:
        print("Defina GITHUB_REPOSITORY, PR_NUMBER e GITHUB_TOKEN.", file=sys.stderr)
        return 1

    pr_number = int(pr_raw)
    full_path = root / "api-validator-report.md"
    public_path = root / "api-validator-report-public.md"

    if not full_path.is_file():
        print(f"Falta {full_path}", file=sys.stderr)
        return 1

    full_text = full_path.read_text(encoding="utf-8")
    if public_path.is_file():
        public_text = public_path.read_text(encoding="utf-8")
    else:
        public_text = full_text

    upsert_review_comment(repo, pr_number, public_text, token)
    block_label = os.environ.get("API_VALIDATOR_BLOCK_LABEL", "Alteração Necessária")
    sync_block_label(repo, pr_number, full_text, block_label, token)

    if _is_nao_aprovavel(full_text):
        print("Conclusao NAO APROVAVEL — job falhou.", file=sys.stderr)
        return 1

    print("Relatorio publicado na PR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
