# Overlay de vizinhos — e-Simples (Java/Spring)

Complementa [`docs/validador/processo/revisao.md`](../../../../docs/validador/processo/revisao.md) após instalar com stack `java-spring-esimples`. Copiado para `docs/validador/revisao.overlay.md` no projeto.

---

# Guia da revisão de API (validador) — linhas e-Simples

Fluxo de revisão: **escopo primeiro**, achados **concretos**, sem lista de melhorias genéricas.

## Fluxo

1. Ter **SPEC** (`docs/SPEC.md` na branch ou texto no `/api-validator`).
2. Roteiro **validador inteligente**: [`processo/inteligente.md`](processo/inteligente.md).
3. **Escopo ampliado:** [`processo/escopo-e-rest.md`](processo/escopo-e-rest.md).
4. `git diff` no escopo da branch (+ REST/SPEC se ampliado).
5. Classificar tipo → escolher **um** vizinho + **um** doc (tabela abaixo).
6. Checklist: [`processo/review-checklist-api.md`](processo/review-checklist-api.md).
7. Ruído: [`processo/nao-reportar.md`](processo/nao-reportar.md).
8. Reportar **Crítico** / **Importante** + **Conclusão** (formato do agente).

## Tipo de atividade → referência

| Tipo | Doc | Vizinho de código |
|------|-----|-------------------|
| Conta a pagar/receber — adicionais no título | `docs/conta-pagar-adicionais.md` | `ContaPagarService`, `ContaPagarRequest` |
| Padrão C (listagem) + filho no pai | `docs/padrao/colecao-filha-vinculada-pai.md` | `ContaReceberMapper.toResponseListagem`, `ContaPagarService.sincronizarPagamentos` |
| Catálogo + fiscal serviço | doc da feature / SPEC | `CatalogoService`, `CatalogoRequest.validar()` |
| Catálogo central (tipo documento) | `docs/tipo-documento-financeiro.md` | `CentralTipoDocumentoFinanceiroService` |
| Permissões | `docs/migrations-permissoes.md` | `V52`-like + `DynamicRoutePermissionFilterTest` |
| CRUD cadastro tenant | `docs/modulo-cadastros.md` | `BancoController` / `EntidadeController` |
| DTO / contrato JSON (request, response, filter) | `docs/padrao/dtos.md` | `BancoRequest`, `ContaPagarRequest`, `ContaPagarMapper` |
| Listagem `listar` (filtro + página) | `docs/padrao/listagem-paginada-filtrada.md` | `EntidadeFilter`, `EntidadeController.listar` |
| Controller / REST fino | `docs/padrao/controllers.md` | `EntidadeController`, `BancoController` |
| Service / regra de negócio | `docs/padrao/services.md` | `BancoService`, `CatalogoService`, `ContaPagarService` |
| Nomenclatura PT (método, model, coluna) | `docs/padrao/nomenclatura-portugues.md` | `Banco.java`, `BancoService`, `EV-NOM-003` |
| Vínculo filho (ex. cliente superior / dependente) | SPEC + `docs/padrao/colecao-filha-vinculada-pai.md` | Sub-rota em `Entidade*Controller`, `docs/padrao/nomenclatura-colunas-sql.md` |
| Importação de contrato (PDF / prévia) | SPEC da tarefa | `ContratoImportacaoController`, `ContratoImportacaoService` |
| Domínio fiscal catálogo (LC 116, NBS, IBS) | SPEC da tarefa | `CatalogoFiscalDominioController`, `CatalogoRequest.validar()` |

## Tríade migration (quando há `db/migration` no diff)

1. Colunas e tipos na SQL  
2. `@Column` / entity  
3. DTO (`@Size`, enums) + `validar()` no service ou request — ver [`docs/padrao/dtos.md`](../padrao/dtos.md)  

Ausência de CHECK na SQL **não** é achado se a API validar (padrão do repo).

## Mapeamento gravidade ↔ relatório

| Seção do relatório | Regras típicas |
|--------------------|----------------|
| **Crítico** | `EV-*` CRÍTICO, tenant, segurança, migration versionada destruída no diff |
| **Importante** | `EV-REST-006/007`, `EV-VAL-004`, SPEC não atendida, teste/compilação quebrada, DDL sem espelho na API |

## Comando

`/api-validator` + escopo; para features com API/front, copiar `docs/SPEC.md` na branch e citar escopo ampliado:

```text
/api-validator #430 — docs/SPEC.md, escopo ampliado REST e aceite, diff vs develop
```
