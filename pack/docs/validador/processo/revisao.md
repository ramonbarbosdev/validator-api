# Guia da revisão de API (validador)

Fluxo: **escopo primeiro**, achados **concretos**.

## Fluxo

1. **SPEC** (`docs/SPEC.md` ou texto no `/api-validator`).
2. [`inteligente.md`](inteligente.md)
3. [`escopo-e-rest.md`](escopo-e-rest.md) — escopo ampliado?
4. `git diff` no escopo (+ REST/SPEC se ampliado).
5. Tipo → **um** vizinho + **um** doc (tabelas abaixo).
6. [`review-checklist-api.md`](review-checklist-api.md)
7. [`nao-reportar.md`](nao-reportar.md)
8. Auth/erros no diff: [`../critico/consumidor-api.md`](../critico/consumidor-api.md) + [`../importante/consumidor-api.md`](../importante/consumidor-api.md) → depois [`../melhoria-ajuste/consumidor-api.md`](../melhoria-ajuste/consumidor-api.md)
9. Relatório: **Crítico** / **Importante** / **Melhoria / Ajuste** / **Conclusão**

Se existir [`revisao.overlay.md`](revisao.overlay.md) no projeto, **mesclar** com a tabela deste arquivo (vizinhos do domínio).

## Tipo de atividade → referência (base Java/Spring)

| Tipo | Doc | Vizinho de código (ajustar ao repo) |
|------|-----|-------------------------------------|
| CRUD cadastro | `docs/padrao/controllers.md` | `*Controller` + `*Service` do módulo |
| DTO / JSON | `docs/padrao/dtos.md` | `*Request`, `*Response`, `*Mapper` |
| Listagem | `docs/padrao/listagem-paginada-filtrada.md` | `*Filter`, `Pageable`, headers |
| Controller fino | `docs/padrao/controllers.md` | Controller sem repository |
| Service | `docs/padrao/services.md` | `*Service` + repositories |
| Nomenclatura PT | `docs/padrao/nomenclatura-portugues.md` | Entity + migration |
| Banco / migration / entity | `docs/padrao/banco.md` | `db/migration`, `TenantEntity` |
| DDL / colunas | `docs/padrao/nomenclatura-colunas-sql.md` | `V*.sql`, `@Column` |
| Permissões / central | doc do projeto | migration `db/central`, testes de rota |
| Multi-tenant | `.cursor/rules/multi-tenant.mdc` | `TenantContextService`, queries |

## Migration — dados primeiro

Diff com `V*.sql`: conferir `EV-PER-006` e seção **Prioridade: dados** em [`banco.md`](../../padrao/banco.md) antes de nomenclatura estética.

## Tríade migration

1. SQL  
2. Entity `@Column`  
3. DTO / `validar()` / service — [`dtos.md`](../../padrao/dtos.md)

## Comando

```text
/api-validator docs/SPEC.md — escopo ampliado, diff vs develop
```
