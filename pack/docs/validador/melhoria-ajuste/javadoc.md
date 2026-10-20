# Melhoria / Ajuste — JavaDoc

Quando **já existe** `/** … */` no método/classe do diff, mas a padronização pode melhorar. Ref.: [`../../padrao/services.md`](../../padrao/services.md).

| Situação | Critério |
|----------|----------|
| Resumo vago | Sem efeito, tenant ou exceções |
| `@param` / `@return` | Parâmetros/retorno relevantes sem tags |
| `@author` / `@since` | Ausentes em código novo (`EV-SVC-005`) |
| `{@link}` | Exceções/services só no texto corrido |
| Desatualizado | Texto não bate com assinatura após o diff |

**Não reportar:** método legado não tocado; ausência total de JavaDoc → [`../importante/codigo-javadoc-comentarios.md`](../importante/codigo-javadoc-comentarios.md).

## Formato do item

* **JavaDoc incompleto em `FooService.bar`**
  * **Onde:** arquivo
  * **Gap:** ex. falta `@param id`, sem `@since`
  * **Ajuste:** modelo `BancoService` / `AuthRefreshTokenService` em `services.md`
