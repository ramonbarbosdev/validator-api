"""GitHub: assinatura de webhook e API minima."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import subprocess
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_VERSION = "2022-11-28"
REVIEW_MARKER = "<!-- review -->"
RUN_MARKER = "<!-- api-validator-run -->"


def _new_comment_each_run() -> bool:
    raw = os.environ.get("API_VALIDATOR_NEW_COMMENT_EACH_RUN", "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def verify_webhook_signature(body: bytes, signature_header: str | None, secret: str) -> bool:
    if not secret:
        return False
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    got = signature_header.removeprefix("sha256=").strip()
    return hmac.compare_digest(expected, got)


def resolve_token() -> str:
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "REVIEW_BOT_TOKEN"):
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
        if out:
            return out
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    raise RuntimeError("Defina GITHUB_TOKEN ou `gh auth login`.")


def api_request(method: str, url: str, token: str, data: dict | None = None) -> Any:
    body = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
    }
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {e.code}: {detail}") from e


def fetch_pr(repo: str, pr_number: int, token: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    return api_request("GET", url, token)


def upsert_validation_started_comment(
    repo: str,
    pr_number: int,
    token: str,
    *,
    sha: str = "",
    pr_html_url: str = "",
) -> None:
    """Comentario na PR quando a validacao comeca (upsert pelo RUN_MARKER)."""
    short = (sha or "?")[:12]
    if sha:
        commit_ref = f"[`{short}`](https://github.com/{repo}/commit/{sha})"
    else:
        commit_ref = f"`{short}`"
    extra = f" — [abrir PR]({pr_html_url})" if pr_html_url else ""
    body = (
        f"{RUN_MARKER}\n"
        f"Validação iniciada para o commit {commit_ref}{extra}.\n\n"
        f"O relatório será publicado nesta PR ao concluir."
    )
    issue_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    comments = api_request("GET", issue_url, token) or []
    for c in comments:
        if RUN_MARKER in (c.get("body") or ""):
            cid = c["id"]
            patch_url = f"https://api.github.com/repos/{repo}/issues/comments/{cid}"
            api_request("PATCH", patch_url, token, {"body": body})
            return
    api_request("POST", issue_url, token, {"body": body})


def upsert_review_comment(repo: str, pr_number: int, body: str, token: str) -> None:
    if REVIEW_MARKER not in body:
        body = f"{REVIEW_MARKER}\n{body}"
    issue_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    if not _new_comment_each_run():
        comments = api_request("GET", issue_url, token) or []
        for c in comments:
            if REVIEW_MARKER in (c.get("body") or ""):
                cid = c["id"]
                patch_url = f"https://api.github.com/repos/{repo}/issues/comments/{cid}"
                api_request("PATCH", patch_url, token, {"body": body})
                return
    api_request("POST", issue_url, token, {"body": body})


def _norm_report(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    return folded.encode("ascii", "ignore").decode().lower()


def parse_report_verdict(report_text: str) -> str | None:
    """Retorna 'aprovavel' ou 'nao aprovavel' (None se nao houver veredito)."""
    nbody = _norm_report(report_text)
    m = re.search(
        r"conclus[aã]o\s*:?\s*"
        r"(nao\s+aprov[aá]vel|aprov[aá]vel\s+com\s+ressalvas|aprov[aá]vel)\b",
        nbody,
    )
    if not m:
        m = re.search(
            r"(?m)^##\s*conclus[aã]o\s*\n\s*"
            r"(nao\s+aprov[aá]vel|aprov[aá]vel\s+com\s+ressalvas|aprov[aá]vel)\s*$",
            nbody,
        )
    if not m:
        return None
    raw = m.group(1)
    if "nao" in raw or "ressalvas" in raw:
        return "nao aprovavel"
    return "aprovavel"


def sync_block_label(repo: str, pr_number: int, report_text: str, block_label: str, token: str) -> None:
    """Apos o comentario de review: APROVAVEL remove a label; caso contrario aplica."""
    label = (block_label or "Alteração Necessária").strip()
    if not label:
        return
    labels_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
    verdict = parse_report_verdict(report_text)
    if verdict == "aprovavel":
        del_url = (
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels/"
            f"{urllib.parse.quote(label)}"
        )
        try:
            api_request("DELETE", del_url, token)
        except RuntimeError:
            pass
        return
    api_request("POST", labels_url, token, [label])
