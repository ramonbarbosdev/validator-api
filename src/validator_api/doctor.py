"""Verificacoes de ambiente antes de servir ou validar."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from validator_api.config import PrReviewConfig, bundled_pack_root, default_env_file, load_env_file
from validator_api.github import resolve_token


def run_doctor() -> int:
    load_env_file()
    env_path = default_env_file()
    issues: list[str] = []
    ok_notes: list[str] = []

    if env_path.is_file():
        ok_notes.append(f"env: {env_path}")
    else:
        issues.append(f"Arquivo .env nao encontrado (esperado em {env_path})")

    try:
        cfg = PrReviewConfig.from_env()
    except Exception as e:
        print(f"Config invalida: {e}", file=sys.stderr)
        return 1

    if not cfg.repository or "/" not in cfg.repository:
        issues.append("GITHUB_REPOSITORY invalido ou ausente")
    else:
        ok_notes.append(f"repo: {cfg.repository}")

    if not (cfg.app_dir / "pom.xml").is_file():
        issues.append(f"REPO_ROOT sem pom.xml: {cfg.app_dir}")
    else:
        ok_notes.append(f"app: {cfg.app_dir}")

    install_sh = cfg.validator_root / "install" / "install.sh"
    install_ps1 = cfg.validator_root / "install" / "install.ps1"
    if not install_sh.is_file() and not install_ps1.is_file():
        issues.append(f"Pacote validador nao encontrado: {cfg.validator_root}")
    else:
        ok_notes.append(f"validator pack: {cfg.validator_root}")
    bundled = bundled_pack_root()
    if bundled.is_dir() and bundled.resolve() == cfg.validator_root.resolve():
        ok_notes.append("usando pack/ embutido no validator-api")

    ci = cfg.validator_root / "scripts" / "ci-api-validator.py"
    if not ci.is_file():
        issues.append(f"Falta ci-api-validator.py em {cfg.validator_root}")
    else:
        ok_notes.append("ci-api-validator.py presente")

    if not os.environ.get("CURSOR_API_KEY", "").strip():
        issues.append("CURSOR_API_KEY ausente")
    else:
        ok_notes.append("CURSOR_API_KEY definido")

    try:
        resolve_token()
        ok_notes.append("GitHub token OK")
    except RuntimeError as e:
        issues.append(str(e))

    if not shutil.which("git"):
        issues.append("git nao esta no PATH")
    else:
        ok_notes.append("git no PATH")

    if shutil.which("gh"):
        ok_notes.append("gh no PATH")
    else:
        ok_notes.append("gh ausente (checkout via git+token ainda funciona)")

    if sys.platform == "win32":
        wsl = cfg.validator_root / "scripts" / "ci-api-validator-cloud-wsl.ps1"
        if wsl.is_file():
            ok_notes.append("Windows: usara WSL para agente cloud")
        else:
            issues.append("Windows sem ci-api-validator-cloud-wsl.ps1")

    state_dir = cfg.state_path.parent
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        test = state_dir / ".write-test"
        test.write_text("ok", encoding="utf-8")
        test.unlink()
        ok_notes.append(f"estado gravavel: {state_dir}")
    except OSError as e:
        issues.append(f"Nao foi possivel gravar em {state_dir}: {e}")

    if not cfg.runner_api_token:
        ok_notes.append("RUNNER_API_TOKEN vazio (ok em dev local; obrigatorio na VPS)")

    print("validator-api doctor\n")
    for line in ok_notes:
        print(f"  OK  {line}")
    for line in issues:
        print(f"  !!  {line}")

    if issues:
        print(f"\n{len(issues)} problema(s).")
        return 1
    print("\nAmbiente pronto.")
    return 0
