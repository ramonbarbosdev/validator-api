#!/usr/bin/env python3
"""Ultimo relatorio do api-validator publicado na PR (comentario <!-- review -->)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from pr_human_comments import REVIEW_MARKERS, _paginate, _parse_repo_slug, _resolve_token


def _enabled() -> bool:
    raw = os.environ.get("CURSOR_VALIDATOR_PREVIOUS_REPORT", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _max_chars() -> int:
    try:
        return max(500, int(os.environ.get("CURSOR_VALIDATOR_PREVIOUS_REPORT_MAX_CHARS", "8000")))
    except ValueError:
        return 8000


def fetch_latest_validator_report_body(pr_number: int) -> str:
    if not _enabled():
        return ""
    slug = _parse_repo_slug()
    if not slug:
        return ""
    token = _resolve_token()
    if not token:
        print(
            "AVISO: sem GITHUB_TOKEN/GH_TOKEN para relatorio anterior da PR; pulando.",
            file=sys.stderr,
        )
        return ""

    owner, repo = slug
    base = f"https://api.github.com/repos/{owner}/{repo}"
    candidates: list[tuple[str, str]] = []

    try:
        for row in _paginate(f"{base}/issues/{pr_number}/comments?per_page=100", token):
            body = str(row.get("body") or "").strip()
            if not body or not any(m in body for m in REVIEW_MARKERS):
                continue
            when = str(row.get("updated_at") or row.get("created_at") or "")
            candidates.append((when, body))
    except OSError as e:
        print(f"AVISO: falha ao buscar relatorio anterior na PR: {e}", file=sys.stderr)
        return ""

    if not candidates:
        return ""
    candidates.sort(key=lambda pair: pair[0])
    return candidates[-1][1]


def format_previous_report_markdown(raw_body: str) -> str:
    body = raw_body.strip()
    if not body:
        return ""
    for marker in REVIEW_MARKERS:
        body = body.replace(marker, "").strip()
    budget = _max_chars()
    truncated = False
    if len(body) > budget:
        body = body[: budget - 80].rstrip() + "\n\n_(Relatorio anterior truncado.)_\n"
        truncated = True
    lines = [
        "## Relatorio anterior do api-validator (ultima publicacao nesta PR)",
        "",
        "Regressao de achados: para cada item **Critico** ou **Importante** abaixo, confira no diff atual.",
        "Corrigido no codigo -> **nao repita** em Critico/Importante; liste em `## Conferencia da rodada anterior` como `- [x]` com arquivo do diff.",
        "Ainda presente -> Critico/Importante de novo, com evidencia.",
        "Itens em Melhoria/Ajuste: repita so se ainda aplicavel; nao reabra so porque constavam aqui.",
        "Achados novos exigem evidencia no diff/SPEC (nao copie o texto antigo sem verificar).",
        "",
        body,
        "",
    ]
    if truncated:
        lines.insert(-1, f"_(Limite ~{_max_chars()} caracteres.)_")
    return "\n".join(lines).strip() + "\n"


def load_pr_previous_report_markdown(pr_number: int | None = None) -> str:
    if not _enabled():
        return ""
    pr_raw = os.environ.get("PR_NUMBER", "").strip()
    if pr_number is None and pr_raw.isdigit():
        pr_number = int(pr_raw)
    if pr_number is None or pr_number <= 0:
        return ""
    raw = fetch_latest_validator_report_body(pr_number)
    return format_previous_report_markdown(raw)


def write_sidecar(root: Path, pr_number: int, markdown: str) -> Path | None:
    if not markdown.strip():
        return None
    out_dir = root / ".api-validator-review"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"pr-{pr_number}-previous-report.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def main() -> int:
    pr_raw = os.environ.get("PR_NUMBER", "").strip()
    if not pr_raw.isdigit():
        print("Defina PR_NUMBER.", file=sys.stderr)
        return 1
    md = load_pr_previous_report_markdown(int(pr_raw))
    if md:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
