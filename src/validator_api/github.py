"""GitHub: assinatura de webhook e API minima."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import subprocess
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_VERSION = "2022-11-28"
REVIEW_MARKER = "<!-- review -->"


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


def sync_block_label(repo: str, pr_number: int, report_text: str, block_label: str, token: str) -> None:
    label = (block_label or "Alteração Necessária").strip()
    if not label:
        return
    norm = unicodedata.normalize("NFD", report_text)
    for ch in ("\u0300", "\u0301", "\u0302", "\u0303", "\u0308"):
        norm = norm.replace(ch, "")
    low = norm.lower()
    nao = "nao aprovavel" in low.replace("ã", "a")
    aprovavel = "conclusao:" in low and "aprovavel" in low and not nao
    labels_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
    if nao:
        api_request("POST", labels_url, token, [label])
    elif aprovavel:
        del_url = (
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels/"
            f"{urllib.parse.quote(label)}"
        )
        try:
            api_request("DELETE", del_url, token)
        except RuntimeError:
            pass
