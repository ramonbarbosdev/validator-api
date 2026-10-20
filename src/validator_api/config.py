"""Config da automacao de PR (env + defaults)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def default_env_file() -> Path:
    override = _env("VALIDATOR_API_ENV_FILE")
    if override:
        return Path(override).expanduser()
    cwd = Path.cwd()
    for name in (".env", ".env.pr-review"):
        candidate = cwd / name
        if candidate.is_file():
            return candidate
    return cwd / ".env"


def load_env_file(path: Path | None = None) -> bool:
    """Carrega .env no processo (idempotente)."""
    if path is None:
        path = default_env_file()
    if not path.is_file():
        return False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ[name.strip()] = value.strip()
    return True


@dataclass(frozen=True)
class PrReviewConfig:
    app_dir: Path
    validator_root: Path
    repository: str
    base_branch: str
    block_label: str
    require_label: str
    state_path: Path
    stack: str
    runner_api_token: str

    @classmethod
    def from_env(cls) -> PrReviewConfig:
        app = Path(_env("REPO_ROOT") or _env("APP_DIR") or ".").resolve()
        if not (app / "pom.xml").is_file() and _env("APP_DIR"):
            app = Path(_env("APP_DIR")).resolve()

        vroot = _env("CURSOR_API_VALIDATOR_ROOT") or _env("VALIDATOR_ROOT")
        if vroot:
            validator = Path(vroot).resolve()
        else:
            sibling = app.parent / "cursor-api-validator-java"
            validator = sibling.resolve() if sibling.is_dir() else app / "cursor-api-validator-java"

        repo = _env("GITHUB_REPOSITORY")
        state = app / ".api-validator-review" / "automation-state.json"
        return cls(
            app_dir=app,
            validator_root=validator,
            repository=repo,
            base_branch=_env("GITHUB_BASE_REF", "develop"),
            block_label=_env("API_VALIDATOR_BLOCK_LABEL", "Alteração Necessária"),
            require_label=_env("API_VALIDATOR_REQUIRE_LABEL"),
            state_path=state,
            stack=_env("API_VALIDATOR_STACK", "java-spring-esimples"),
            runner_api_token=_env("RUNNER_API_TOKEN"),
        )
