"""Gate por labels / draft (mesma logica do workflow, sem Actions)."""
from __future__ import annotations

from typing import Any


def _label_names(pr: dict[str, Any]) -> set[str]:
    labels = pr.get("labels") or []
    return {str(x.get("name", "")) for x in labels if x.get("name")}


def is_block_label_removed(payload: dict[str, Any], block_label: str) -> bool:
    """pull_request unlabeled: label removida e o nome e o de bloqueio do validador."""
    if (payload.get("action") or "") != "unlabeled":
        return False
    label = payload.get("label")
    if not isinstance(label, dict):
        return False
    removed = str(label.get("name") or "").strip()
    block = (block_label or "Alteração Necessária").strip()
    return bool(block and removed == block)


def should_validate(
    pr: dict[str, Any],
    *,
    block_label: str,
    require_label: str,
    manual: bool = False,
) -> tuple[bool, str]:
    if manual:
        return True, "disparo manual"

    if pr.get("isDraft") is True:
        return False, "PR em rascunho (draft)"

    names = _label_names(pr)
    block = (block_label or "Alteração Necessária").strip()
    if block and block in names:
        return False, f"PR com label de bloqueio `{block}`"

    req = (require_label or "").strip()
    if req:
        if req in names:
            return True, f"PR com label opt-in `{req}`"
        return False, f"aguardando label `{req}`"

    return True, "sem bloqueio de label"
