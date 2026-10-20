"""Estado local: ultimo SHA validado por PR."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"prs": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_validated_sha(state: dict[str, Any], pr_number: int) -> str | None:
    entry = (state.get("prs") or {}).get(str(pr_number))
    if not entry:
        return None
    return entry.get("validated_sha")


def mark_validated(path: Path, pr_number: int, sha: str) -> None:
    state = load_state(path)
    state.setdefault("prs", {})[str(pr_number)] = {
        "validated_sha": sha,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(path, state)
