#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:?Uso: install.sh /caminho/do/projeto-java [java-spring-esimples]}"
STACK="${2:-}"
PACKAGE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$(cd "$TARGET" && pwd)"

copy_merge() {
  local from="$1" to="$2"
  [[ -d "$from" ]] || return 0
  mkdir -p "$to"
  cp -R "$from"/. "$to"/
}

echo "Instalando cursor-api-validator-java em: $TARGET"

copy_merge "$PACKAGE_ROOT/.cursor" "$TARGET/.cursor"
copy_merge "$PACKAGE_ROOT/docs/validador" "$TARGET/docs/validador"
copy_merge "$PACKAGE_ROOT/docs/padrao" "$TARGET/docs/padrao"
cp -f "$PACKAGE_ROOT/docs/SPEC.template.md" "$TARGET/docs/SPEC.template.md"

if [[ "$STACK" == "java-spring-esimples" ]]; then
  STACK_ROOT="$PACKAGE_ROOT/stacks/java-spring-esimples"
  copy_merge "$STACK_ROOT/docs/padrao" "$TARGET/docs/padrao"
  cp -f "$STACK_ROOT/docs/validador/revisao.overlay.md" "$TARGET/docs/validador/revisao.overlay.md"
  echo "Stack java-spring-esimples aplicado."
fi

echo "Concluido. Revise templates/AGENTS.snippet.md e commit .cursor + docs."
