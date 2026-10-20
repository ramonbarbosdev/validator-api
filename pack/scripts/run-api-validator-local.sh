#!/usr/bin/env bash
# Validacao via cursor-sdk LOCAL (Linux/WSL). Requer CURSOR_API_KEY no .env ou ambiente.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -z "${CURSOR_API_VALIDATOR_ROOT:-}" ]]; then
  export CURSOR_API_VALIDATOR_ROOT="$VALIDATOR_ROOT"
fi

BASE="${GITHUB_BASE_REF:-develop}"
git fetch origin "$BASE" 2>/dev/null || true
bash "$VALIDATOR_ROOT/install/install.sh" "$(pwd)" java-spring-esimples

if [[ ! -f pom.xml ]]; then
  echo "Execute na raiz do esimples-api (pom.xml)." >&2
  exit 1
fi

export REPO_ROOT="$(pwd)"
export CURSOR_VALIDATOR_RUNTIME=local
export CURSOR_VALIDATOR_FORCE_LOCAL=1

python3 -m pip install -q -r "$VALIDATOR_ROOT/scripts/requirements-ci.txt"

echo "Executando api-validator (SDK local, WSL/Linux)..."
echo "REPO_ROOT=$REPO_ROOT"
python3 "$VALIDATOR_ROOT/scripts/ci-api-validator.py"

if [[ -f "$REPO_ROOT/api-validator-report.md" ]]; then
  echo ""
  echo "=== RELATORIO ==="
  cat "$REPO_ROOT/api-validator-report.md"
fi
