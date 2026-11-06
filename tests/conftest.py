"""Configuracao compartilhada dos testes do validador."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack"

for _p in (PACK / "scripts", PACK / "checks", ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


class GitRepo:
    """Repo git temporario com `origin/<base>` apontando para o commit inicial."""

    def __init__(self, path: Path, base: str = "develop") -> None:
        self.path = path
        self.base = base
        _git(path, "init", "-q", "-b", base)
        _git(path, "config", "user.email", "teste@example.com")
        _git(path, "config", "user.name", "Teste")
        _git(path, "config", "core.autocrlf", "false")
        (path / "README.md").write_text("base\n", encoding="utf-8")
        self.commit("base")
        _git(path, "update-ref", f"refs/remotes/origin/{base}", "HEAD")

    def write(self, rel: str, content: str) -> None:
        """Grava arquivo relativo ao repo (cria pastas)."""
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")

    def commit(self, message: str) -> str:
        """Commita tudo e retorna o SHA."""
        _git(self.path, "add", "-A")
        _git(self.path, "commit", "-q", "--allow-empty", "-m", message)
        return _git(self.path, "rev-parse", "HEAD").strip()

    def git(self, *args: str) -> str:
        return _git(self.path, *args)


@pytest.fixture
def git_repo(tmp_path: Path) -> GitRepo:
    """Repo git com base `develop` publicada como `origin/develop`."""
    return GitRepo(tmp_path / "api")
