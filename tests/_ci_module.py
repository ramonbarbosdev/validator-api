"""Carrega pack/scripts/ci-api-validator.py (nome com hifen) como modulo e argumentos fixos de prompt."""
from __future__ import annotations

import importlib.util
from pathlib import Path

CI_PATH = Path(__file__).resolve().parent.parent / "pack" / "scripts" / "ci-api-validator.py"
SNAPSHOT = Path(__file__).resolve().parent / "snapshots" / "prompt_sem_checks.txt"


def load_ci_module():
    """Importa o script do CI sem executar `main`."""
    spec = importlib.util.spec_from_file_location("ci_api_validator", CI_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prompt_kwargs() -> dict:
    """Argumentos deterministas cobrindo os blocos dinamicos do prompt."""
    return {
        "root": Path("repo"),
        "base": "develop",
        "pr_label": "PR #541",
        "stat": " src/main/java/A.java | 3 ++-\n 1 file changed",
        "spec_line": "Sem docs/SPEC.md na branch: gate enxuto (somente git diff vs base).",
        "cloud": True,
        "pr_discussion": "## Discussao na PR\n- autor: ok",
        "pr_previous_report": "## Critico\n\nNenhum.\n\n## Importante\n\n* **Gap**",
        "filho_pai_checklist": True,
        "filho_pai_code_facts": "### Fatos\n- x",
        "changed_files": ["src/main/java/A.java", "src/main/java/B.java"],
    }


def build_default_prompt(module) -> str:
    """Prompt com os argumentos fixos e sem kwargs novos (comportamento legado)."""
    kwargs = prompt_kwargs()
    return module.build_prompt(
        kwargs.pop("root"), kwargs.pop("base"), kwargs.pop("pr_label"),
        kwargs.pop("stat"), kwargs.pop("spec_line"), **kwargs,
    )
