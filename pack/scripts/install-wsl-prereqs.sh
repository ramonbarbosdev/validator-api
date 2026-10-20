#!/usr/bin/env bash
# Pré-requisitos WSL (Ubuntu) para ci-api-validator-cloud-wsl.ps1 no runner Windows.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="${HOME}/.cache/api-validator-ci-venv"
REQ="${VALIDATOR_ROOT}/scripts/requirements-ci.txt"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Execute dentro do WSL/Linux (ou use install-wsl-prereqs.ps1 no Windows)." >&2
  exit 1
fi

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [[ "${ID:-}" == "ubuntu" || "${ID_LIKE:-}" == *debian* ]]; then
    if ! command -v python3 >/dev/null 2>&1 || ! python3 -m venv --help >/dev/null 2>&1; then
      echo "Instalando pacotes (sudo)..."
      sudo apt update
      sudo apt install -y python3 python3-venv python3-pip git
    fi
  else
    echo "AVISO: distro nao Ubuntu/Debian; instale python3, venv e pip manualmente." >&2
  fi
fi

if [[ ! -f "$REQ" ]]; then
  echo "Nao encontrei $REQ" >&2
  exit 1
fi

if [[ ! -x "${VENV}/bin/python" ]]; then
  echo "Criando venv em ${VENV}..."
  python3 -m venv "$VENV"
fi

PY="${VENV}/bin/python"
"$PY" -m pip install -q -U pip
"$PY" -m pip install -q -r "$REQ"

echo ""
echo "OK: WSL pronto para api-validator (cloud via WSL)."
echo "  Python: $("$PY" --version)"
echo "  Venv:   ${VENV}"
echo "  Teste:  CURSOR_API_KEY=... REPO_ROOT=/mnt/c/.../esimples-api \\"
echo "          CURSOR_VALIDATOR_RUNTIME=cloud \"$PY\" ${VALIDATOR_ROOT}/scripts/ci-api-validator.py"
