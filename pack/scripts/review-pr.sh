#!/usr/bin/env bash
# Prepara checkout da PR, install do validador e artefatos para /api-validator.
set -euo pipefail

APP_DIR=""
PR=""
BASE="develop"
STACK="java-spring-esimples"
PACKAGE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  echo "Uso: $0 --app-dir PATH --pr NUMBER [--base develop] [--stack java-spring-esimples]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-dir) APP_DIR="$2"; shift 2 ;;
    --pr) PR="$2"; shift 2 ;;
    --base) BASE="$2"; shift 2 ;;
    --stack) STACK="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Argumento desconhecido: $1"; usage ;;
  esac
done

[[ -n "$APP_DIR" && -n "$PR" ]] || usage
[[ -d "$APP_DIR/.git" ]] || { echo "Erro: --app-dir não é repositório git: $APP_DIR"; exit 1; }

OUT_DIR="$APP_DIR/.api-validator-review"
mkdir -p "$OUT_DIR"

cd "$APP_DIR"

PR_TITLE=""
PR_BODY=""
if command -v gh >/dev/null 2>&1; then
  PR_TITLE="$(gh pr view "$PR" --json title -q .title 2>/dev/null || true)"
  PR_BODY="$(gh pr view "$PR" --json body -q .body 2>/dev/null || true)"
  gh pr checkout "$PR" --force 2>/dev/null || gh pr checkout "$PR"
else
  echo "Aviso: gh não encontrado; usando git fetch pull/$PR/head"
  git fetch origin "pull/$PR/head:refs/heads/api-validator-pr-$PR"
  git checkout "api-validator-pr-$PR"
fi

git fetch origin "$BASE" 2>/dev/null || true
BASE_REF="origin/$BASE"
if ! git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  BASE_REF="$BASE"
fi

HEAD_SHA="$(git rev-parse HEAD)"
DIFF_STAT="$(git diff --stat "$BASE_REF...HEAD" 2>/dev/null || git diff --stat "$BASE_REF" HEAD)"
git diff "$BASE_REF...HEAD" > "$OUT_DIR/pr-${PR}-diff.patch" 2>/dev/null || git diff "$BASE_REF" HEAD > "$OUT_DIR/pr-${PR}-diff.patch"

bash "$PACKAGE_ROOT/install/install.sh" "$APP_DIR" "$STACK"

SPEC_PATH=""
if [[ -f "$APP_DIR/docs/SPEC.md" ]]; then
  SPEC_PATH="docs/SPEC.md"
elif [[ -n "$PR_BODY" ]]; then
  if echo "$PR_BODY" | grep -qE 'docs/SPEC[^[:space:]]*\.md'; then
    SPEC_PATH="$(echo "$PR_BODY" | grep -oE 'docs/SPEC[^[:space:]]*\.md' | head -1)"
  fi
fi

printf '{"pr":%s,"base":"%s","base_ref":"%s","head_sha":"%s","spec_path":"%s","stack":"%s"}\n' \
  "$PR" "$BASE" "$BASE_REF" "$HEAD_SHA" "$SPEC_PATH" "$STACK" > "$OUT_DIR/pr-${PR}-meta.json"

{
  echo "# Prompt — api-validator (PR #$PR)"
  echo
  [[ -n "$PR_TITLE" ]] && echo "**Título:** $PR_TITLE"
  echo "**Base:** \`$BASE_REF\` · **HEAD:** \`$HEAD_SHA\`"
  echo
  echo "Execute como usuário no Cursor (somente relatório, sem alterar código):"
  echo
  echo '```text'
  echo "/api-validator PR #$PR — diff vs $BASE_REF."
  if [[ -n "$SPEC_PATH" ]]; then
    echo "SPEC: $SPEC_PATH — escopo ampliado se houver Contrato HTTP; validador inteligente."
  else
    echo "Sem docs/SPEC.md na branch: gate enxuto (só diff), salvo escopo no corpo da PR."
  fi
  echo "Seguir .cursor/agents/api-validator.md e .cursor/skills/revisao-api/SKILL.md."
  echo '```'
  echo
  echo "## git diff --stat"
  echo '```'
  echo "$DIFF_STAT"
  echo '```'
  echo
  echo "Diff completo: \`.api-validator-review/pr-${PR}-diff.patch\`"
  if [[ -n "$PR_BODY" ]]; then
    echo
    echo "## Corpo da PR (referência)"
    echo "$PR_BODY"
  fi
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  export PR_NUMBER="$PR"
  if [[ -z "${GITHUB_REPOSITORY:-}" ]] && command -v gh >/dev/null 2>&1; then
    GITHUB_REPOSITORY="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
    export GITHUB_REPOSITORY
  fi
  if command -v python3 >/dev/null 2>&1; then
    DISCUSSION="$(python3 "$SCRIPT_DIR/pr_human_comments.py" 2>/dev/null || true)"
    if [[ -n "$DISCUSSION" ]]; then
      printf '%s\n' "$DISCUSSION" > "$OUT_DIR/pr-${PR}-discussion.md"
      echo
      echo "$DISCUSSION"
    fi
  fi
} > "$OUT_DIR/pr-${PR}-prompt.md"

echo "OK: $OUT_DIR/pr-${PR}-prompt.md"
echo "Checkout: $(git branch --show-current) @ $HEAD_SHA"
