# Validador — não reportar (ruído conhecido)

Lista de situações que **não** entram em Crítico/Importante no `/api-validator`, salvo se a SPEC da tarefa exigir o contrário.

## Persistência e DTO

- `@Size` ausente no DTO quando `validar()` ou o service já limita o campo no caminho de persistência.
- `CHECK` ausente na migration quando a API valida o mesmo domínio no fluxo de escrita.
- Swagger / OpenAPI ausente ou incompleto.

## Testes

- Falta de teste novo (`EV-TST-*`) sem teste do escopo falhando e sem critério de aceite na SPEC.
- Falta de `@WebMvcTest` para endpoint novo se a SPEC não exigir.

## Git e escopo

- `V*.sql` deletada só na working tree, fora do `git diff origin/develop...HEAD`.
- Arquivos não relacionados na working tree.

## Código e estilo

- “Poderia extrair método”, Optional, interface nova, clean code.
- Rename ou imports só por formatação.
- N+1 / EntityGraph sem falha demonstrada no escopo.
- JavaDoc ausente em classe/método **não alterado** pelo diff (legado).
- Falta só `@author`/`@since` quando o bloco `/**` já descreve o método — opcional em Melhoria; não elevar a Importante só por isso.

## Documentação

- `docs/arquitetura-banco-atual.md` desatualizada em relação ao banco (referência interna, não item de correção da atividade).

## Front-end (repositório do SPA)

- CSS, layout, componente React, roteamento, estado do front — **não** em Crítico/Importante.
- Mensagem/status **definidos pela API** no diff (handler, `ApiErrorResponse`, auth) → avaliar em **Melhoria / Ajuste** ([`../melhoria-ajuste/consumidor-api.md`](../melhoria-ajuste/consumidor-api.md)), não aqui.

## Quando algo desta lista **vira** achado

- A SPEC ou critério de aceite pede explicitamente (ex.: “teste de controller para novo GET”).
- O diff introduz regressão comprovada (ex.: whitelist sem plano para dado legado **e** aceite cita edição de cadastro antigo).
- Regra `EV-*` **CRÍTICA** ou **IMPORTANTE** com evidência no fluxo, independente desta lista.

Atualize este arquivo quando o time fechar uma convenção no chat (ver `.cursor/rules/padroes-projeto-via-chat.mdc`).
