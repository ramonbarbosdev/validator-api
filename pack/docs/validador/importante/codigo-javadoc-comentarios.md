# Importante — JavaDoc e comentários no código

Escopo: **código novo ou alterado no diff**. Ref.: [`../../padrao/services.md`](../../padrao/services.md), [`../../padrao/controllers.md`](../../padrao/controllers.md), `EV-SVC-*`, `EV-CTL-*`.

## Vai em **Importante**

| Regra | O que procurar |
|-------|----------------|
| **EV-SVC-003** | `//` ou `/* … */` **dentro do corpo** do método |
| **EV-SVC-002** | Classe `*Service` nova ou método **público novo** sem `/** … */` |
| **EV-SVC-004** | Método novo sem chamadores no projeto |
| Controller | Comentário inline no corpo do endpoint |

Comentário aleatório no meio do código **não** é Melhoria / Ajuste.

## Formato do item

* **Comentário no corpo do método**
  * **Onde:** `FooService.java`, método `bar`
  * **Problema:** `// passo` dentro do método
  * **Impacto:** viola padrão; usar JavaDoc ou método privado nomeado
  * **Correção:** remover comentário; extrair método ou expandir JavaDoc

JavaDoc **presente** mas incompleto → [`../melhoria-ajuste/javadoc.md`](../melhoria-ajuste/javadoc.md).
