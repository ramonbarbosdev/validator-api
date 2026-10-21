"""Servidor HTTP: webhook GitHub, status e API v1."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from validator_api.auth import authorize_request
from validator_api.config import PrReviewConfig, load_env_file
from validator_api.gate import is_block_label_removed, should_validate
from validator_api.github import verify_webhook_signature
from validator_api.queue import QueueJob, get_queue
from validator_api.runner import run_validation

PR_ACTIONS = frozenset(
    {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
        "labeled",
        "unlabeled",
    }
)

STATUS_PATHS = frozenset({"/status", "/api/v1/status"})


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


def _pr_from_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    pr = payload.get("pull_request")
    if not isinstance(pr, dict):
        return None
    labels = pr.get("labels") or []
    return {
        "number": pr.get("number"),
        "head_sha": (pr.get("head") or {}).get("sha"),
        "isDraft": pr.get("draft"),
        "labels": labels,
    }


def _should_process_event(
    payload: dict[str, Any], cfg: PrReviewConfig
) -> tuple[bool, str, int | None, str | None]:
    repo_full = (payload.get("repository") or {}).get("full_name") or ""
    expected = cfg.repository
    if expected and repo_full and repo_full.lower() != expected.lower():
        return False, f"repo ignorado ({repo_full})", None, None

    gh_event = os.environ.get("_CURRENT_GH_EVENT", "")
    action = payload.get("action") or ""

    if gh_event == "pull_request":
        if action not in PR_ACTIONS:
            return False, f"pull_request action ignorada: {action}", None, None
        pr = _pr_from_payload(payload)
        if not pr or not pr.get("number"):
            return False, "sem numero de PR", None, None
        ok, reason = should_validate(
            pr,
            block_label=cfg.block_label,
            require_label=cfg.require_label,
        )
        if not ok:
            return False, reason, int(pr["number"]), pr.get("head_sha")
        return True, reason, int(pr["number"]), pr.get("head_sha")

    if gh_event == "pull_request_review":
        if action != "submitted":
            return False, "review ignorado", None, None
        pr = payload.get("pull_request")
        if not isinstance(pr, dict):
            return False, "sem PR", None, None
        num = pr.get("number")
        if not num:
            return False, "sem numero", None, None
        pr_gate = {
            "isDraft": pr.get("draft"),
            "labels": pr.get("labels") or [],
        }
        ok, reason = should_validate(
            pr_gate,
            block_label=cfg.block_label,
            require_label=cfg.require_label,
        )
        head_sha = (pr.get("head") or {}).get("sha")
        if not ok:
            return False, reason, int(num), head_sha
        return True, f"review submitted ({reason})", int(num), head_sha

    return False, f"evento ignorado: {gh_event}", None, None


def _enqueue_pr(
    pr_num: int,
    *,
    event: str,
    reason: str,
    head_sha: str | None = None,
    force: bool = False,
) -> tuple[int, int]:
    job = QueueJob(
        pr_number=pr_num,
        enqueued_at=datetime.now(timezone.utc).isoformat(),
        event=event,
        reason=reason,
        head_sha=head_sha,
        force=force,
    )
    return get_queue().enqueue(job)


def _cors_origin() -> str:
    return os.environ.get("VALIDATOR_API_CORS_ORIGIN", "").strip()


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "ValidatorApi/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[webhook] {self.address_string()} - {fmt % args}")

    def _apply_cors(self) -> None:
        origin = _cors_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _json_response(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._apply_cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        if not _cors_origin():
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(204)
        self._apply_cors()
        self.end_headers()

    def _unauthorized(self) -> None:
        self.send_response(401)
        self.end_headers()

    def _read_json_body(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    def _status_payload(self) -> dict[str, Any]:
        cfg: PrReviewConfig = self.server.cfg  # type: ignore[attr-defined]
        snap = get_queue().snapshot()
        return {"ok": True, "repository": cfg.repository, **snap}

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]

        if path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return

        if path in STATUS_PATHS:
            if not authorize_request(self):
                self._unauthorized()
                return
            self._json_response(200, self._status_payload())
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        cfg: PrReviewConfig = self.server.cfg  # type: ignore[attr-defined]
        path = self.path.split("?", 1)[0]

        if path == "/api/v1/validate":
            if not authorize_request(self):
                self._unauthorized()
                return
            data = self._read_json_body()
            if data is None:
                self.send_response(400)
                self.end_headers()
                return
            pr_num = data.get("pr_number")
            if not isinstance(pr_num, int):
                try:
                    pr_num = int(pr_num)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    self._json_response(400, {"ok": False, "error": "pr_number obrigatorio"})
                    return
            force = bool(data.get("force"))
            position, pending = _enqueue_pr(
                pr_num,
                event="api/v1/validate",
                reason="disparo manual via API",
                force=force,
            )
            self._json_response(
                202,
                {
                    "ok": True,
                    "queued": True,
                    "pr": pr_num,
                    "queue_position": position,
                    "pending_count": pending,
                },
            )
            return

        if path not in ("/webhook", "/"):
            self.send_response(404)
            self.end_headers()
            return

        secret = _env("GITHUB_WEBHOOK_SECRET", "")
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length)
        sig = self.headers.get("X-Hub-Signature-256")
        event = self.headers.get("X-GitHub-Event", "")

        if secret and not verify_webhook_signature(body, sig, secret):
            self.send_response(401)
            self.end_headers()
            return

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        os.environ["_CURRENT_GH_EVENT"] = event
        action = payload.get("action") or ""
        event_label = f"{event}/{action}" if action else event
        run_it, reason, pr_num, head_sha = _should_process_event(payload, cfg)

        resp: dict[str, Any] = {"ok": True, "queued": False, "event": event_label}
        if pr_num is not None:
            resp["pr"] = pr_num

        if run_it and pr_num:
            force = (
                event == "pull_request"
                and is_block_label_removed(payload, cfg.block_label)
            )
            if force:
                reason = f"{reason}; revalidacao (label de bloqueio removida)"
            position, pending = _enqueue_pr(
                pr_num,
                event=event_label,
                reason=reason,
                head_sha=head_sha,
                force=force,
            )
            print(f"[webhook] {event_label}: PR #{pr_num} -> fila pos {position} ({reason})")
            resp["queued"] = True
            resp["queue_position"] = position
            resp["pending_count"] = pending
        else:
            print(f"[webhook] {event_label}: ignorado — {reason}")
            resp["ignored"] = True
            resp["reason"] = reason

        self._json_response(202, resp)


def serve_http(cfg: PrReviewConfig) -> int:
    host = _env("WEBHOOK_HOST", "0.0.0.0")
    port = int(_env("WEBHOOK_PORT", "8765") or "8765")
    secret = _env("GITHUB_WEBHOOK_SECRET", "")

    if not secret:
        print("AVISO: GITHUB_WEBHOOK_SECRET vazio — assinatura nao sera validada.")
    if not _env("GITHUB_TOKEN", ""):
        print("AVISO: GITHUB_TOKEN vazio — validacao via webhook vai falhar.")

    q = get_queue()

    def _run_pr(pr_number: int, force: bool) -> int:
        load_env_file()
        job_cfg = PrReviewConfig.from_env()
        return run_validation(job_cfg, pr_number, force=force)

    q.start_worker(_run_pr)

    httpd = ThreadingHTTPServer((host, port), ApiHandler)
    httpd.cfg = cfg  # type: ignore[attr-defined]

    print(f"validator-api em http://{host}:{port}/webhook (repo={cfg.repository})")
    print(f"Status: http://{host}:{port}/api/v1/status")
    if cfg.runner_api_token:
        print("RUNNER_API_TOKEN definido — /status e /api/v1/* exigem Bearer.")
    else:
        print("AVISO: RUNNER_API_TOKEN vazio — /status publico (defina em producao).")
    print("ngrok: ngrok http", port)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
    return 0
