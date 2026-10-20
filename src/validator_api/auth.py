"""Autenticacao da API REST (validator-front / VPS)."""
from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler


def configured_token() -> str:
    return os.environ.get("RUNNER_API_TOKEN", "").strip()


def authorize_request(handler: BaseHTTPRequestHandler) -> bool:
    """Se RUNNER_API_TOKEN estiver definido, exige Authorization: Bearer."""
    expected = configured_token()
    if not expected:
        return True
    auth = (handler.headers.get("Authorization") or "").strip()
    if not auth.lower().startswith("bearer "):
        return False
    return auth[7:].strip() == expected
