# Melhoria / Ajuste — consumidor da API (front)

Somente com evidência no diff (handler, `ApiErrorResponse`, validação exposta). Fluxo **funciona**; melhora clareza.

| Situação | Exemplo |
|----------|---------|
| Status HTTP confuso mas documentável | 204 em `/me` + refresh — contrato no handler/doc |
| Mensagem genérica | `SESSION_EXPIRED` pouco acionável quando `erro` já orienta o front |
| `path` / `erro` inconsistente entre endpoints | Mesmo cenário, códigos diferentes |
| Validação 400/422 | `details` vazio ou texto técnico de campo |
| Fluxo login/org/2FA | Corpo poderia indicar próximo passo (cookies HttpOnly) |

**Não reportar:** layout/CSS/React; defeito de tenant/segurança; campo JSON opcional sem impacto na UI.

## Formato do item

* **Título**
  * **Onde:** classe/método
  * **Cenário:** ação do usuário
  * **O que o usuário vê hoje:**
  * **Melhoria:** status, `mensagem`/`erro`, ou doc de contrato

## Quando percorrer

Diff em `GlobalExceptionHandler`, `RestAuthenticationEntryPoint`, `AuthController`, `AuthSessionService`, filtros, `ConstraintMessageMap`, `validar()` com mensagem ao cliente.

Auth cookies (esimples): `docs/auth-sessao-cookies.md` no projeto da API, se existir.

Bloqueante: [`../importante/consumidor-api.md`](../importante/consumidor-api.md).
