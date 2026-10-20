"""Gate por labels / draft (mesma logica do workflow, sem Actions)."""
from __future__ import annotations

from typing import Any


def _label_names(pr: dict[str, Any]) -> set[str]:
    labels = pr.get("labels") or []
    return {str(x.get("name", "")) for x in labels if x.get("name")}


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
