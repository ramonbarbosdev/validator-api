#!/usr/bin/env python3
"""Comentarios humanos da PR (issue + review + inline), sem bots / relatorio do validador."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
REVIEW_MARKERS = ("<!-- review -->", "<!-- api-validator -->")
DEFAULT_BOT_LOGINS = frozenset(
    {
        "github-actions",
        "github-actions[bot]",
        "review",
        "review[bot]",
        "cursor[bot]",
        "dependabot",
        "dependabot[bot]",
        "renovate",
        "renovate[bot]",
    }
)


@dataclass(frozen=True)
class CommentItem:
    kind: str
    author: str
    created_at: str
    body: str
    path: str | None = None


def _enabled() -> bool:
    raw = os.environ.get("CURSOR_VALIDATOR_PR_COMMENTS", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _max_chars() -> int:
    try:
        return max(500, int(os.environ.get("CURSOR_VALIDATOR_PR_COMMENTS_MAX_CHARS", "12000")))
    except ValueError:
        return 12000


def _bot_logins() -> set[str]:
    extra = os.environ.get("CURSOR_VALIDATOR_BOT_LOGINS", "").strip()
    logins = set(DEFAULT_BOT_LOGINS)
    if extra:
        for part in extra.split(","):
            p = part.strip()
            if p:
                logins.add(p.lower())
    return logins


def _resolve_token() -> str | None:
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    try:
        out = subprocess.check_output(
            ["gh", "auth", "token"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _is_bot(login: str, body: str) -> bool:
    if not login:
        return True
    low = login.lower()
    if low in _bot_logins():
        return True
    if low.endswith("[bot]"):
        return True
    if any(m in body for m in REVIEW_MARKERS):
        return True
    if "## Review" in body or "## API Validator" in body or "## Código Review" in body:
        return True
    return False


def _github_get(url: str, token: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _paginate(url: str, token: str) -> list[Any]:
    items: list[Any] = []
    next_url: str | None = url
    while next_url:
        req = urllib.request.Request(
            next_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            chunk = json.loads(resp.read().decode("utf-8"))
            if not isinstance(chunk, list):
                return chunk if isinstance(chunk, dict) else items
            items.extend(chunk)
            link = resp.headers.get("Link", "")
            next_url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip().strip("<>")
                    break
    return items


def _parse_repo_slug() -> tuple[str, str] | None:
    slug = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if slug and "/" in slug:
        owner, repo = slug.split("/", 1)
        return owner, repo
    return None


def fetch_comment_items(pr_number: int) -> list[CommentItem]:
    if not _enabled():
        return []
    slug = _parse_repo_slug()
    if not slug:
        return []
    token = _resolve_token()
    if not token:
        print(
            "AVISO: sem GITHUB_TOKEN/GH_TOKEN para comentarios da PR; pulando discussao.",
            file=sys.stderr,
        )
        return []

    owner, repo = slug
    base = f"https://api.github.com/repos/{owner}/{repo}"
    items: list[CommentItem] = []

    try:
        for row in _paginate(f"{base}/issues/{pr_number}/comments?per_page=100", token):
            user = row.get("user") or {}
            login = str(user.get("login") or "")
            body = str(row.get("body") or "").strip()
            if not body or _is_bot(login, body):
                continue
            items.append(
                CommentItem(
                    kind="comentario",
                    author=login,
                    created_at=str(row.get("created_at") or ""),
                    body=body,
                )
            )

        for row in _paginate(f"{base}/pulls/{pr_number}/comments?per_page=100", token):
            user = row.get("user") or {}
            login = str(user.get("login") or "")
            body = str(row.get("body") or "").strip()
            if not body or _is_bot(login, body):
                continue
            path = row.get("path")
            line = row.get("line") or row.get("original_line")
            prefix = f"{path}:{line}" if path else "inline"
            items.append(
                CommentItem(
                    kind=f"review ({prefix})",
                    author=login,
                    created_at=str(row.get("created_at") or ""),
                    body=body,
                    path=str(path) if path else None,
                )
            )

        reviews = _paginate(f"{base}/pulls/{pr_number}/reviews?per_page=100", token)
        if isinstance(reviews, list):
            for row in reviews:
                user = row.get("user") or {}
                login = str(user.get("login") or "")
                body = str(row.get("body") or "").strip()
                if not body or _is_bot(login, body):
                    continue
                state = str(row.get("state") or "")
                items.append(
                    CommentItem(
                        kind=f"review ({state})" if state else "review",
                        author=login,
                        created_at=str(row.get("submitted_at") or row.get("created_at") or ""),
                        body=body,
                    )
                )
    except urllib.error.HTTPError as e:
        print(f"AVISO: GitHub API comentarios PR #{pr_number}: HTTP {e.code}", file=sys.stderr)
        return []
    except OSError as e:
        print(f"AVISO: falha ao buscar comentarios da PR: {e}", file=sys.stderr)
        return []

    items.sort(key=lambda c: c.created_at or "")
    return items


def format_markdown(items: list[CommentItem]) -> str:
    if not items:
        return ""
    lines = [
        "## Discussao na PR (humanos; escopo de negocio)",
        "",
        "Precedencia de escopo (ver secao no api-validator.md): combinados, excecoes e regras de negocio",
        "explicadas pelo time. Use **antes** de criticar desvio de padrao generico.",
        "Achados ainda exigem evidencia no diff/SPEC; seguranca/tenant critico nao e anulado aqui.",
        "",
    ]
    budget = _max_chars()
    used = sum(len(ln) for ln in lines)
    truncated = False
    for it in items:
        when = it.created_at[:10] if it.created_at else "?"
        block = f"### {it.author} · {it.kind} · {when}\n\n{it.body}\n"
        if used + len(block) > budget:
            truncated = True
            break
        lines.append(block)
        used += len(block)
    if truncated:
        lines.append(f"\n_(Trecho truncado em ~{_max_chars()} caracteres.)_\n")
    return "\n".join(lines).strip() + "\n"


def load_pr_discussion_markdown(pr_number: int | None = None) -> str:
    if not _enabled():
        return ""
    pr_raw = os.environ.get("PR_NUMBER", "").strip()
    if pr_number is None and pr_raw.isdigit():
        pr_number = int(pr_raw)
    if pr_number is None or pr_number <= 0:
        return ""
    return format_markdown(fetch_comment_items(pr_number))


def write_sidecar(root: Path, pr_number: int, markdown: str) -> Path | None:
    if not markdown.strip():
        return None
    out_dir = root / ".api-validator-review"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"pr-{pr_number}-discussion.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def main() -> int:
    pr_raw = os.environ.get("PR_NUMBER", "").strip()
    if not pr_raw.isdigit():
        print("Defina PR_NUMBER.", file=sys.stderr)
        return 1
    md = load_pr_discussion_markdown(int(pr_raw))
    if md:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
