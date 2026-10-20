# Checklist de revisão — esimples-api

Uso com `/api-validator` e escopo ampliado ([`escopo-e-rest.md`](escopo-e-rest.md)). Percorra **só as seções** que a SPEC ou o diff tocam. Confiança alta (comportamento ou compilação), não checklist decorativo.

## Antes do diff

- [ ] Escopo: issue + `docs/SPEC.md` na branch ou texto no comando.
- [ ] Modo: gate só diff **ou** escopo ampliado (SPEC / controller / integração).
- [ ] Vizinho escolhido em [`revisao.md`](revisao.md).

## SPEC e entrega

- [ ] Resultado esperado e critérios de aceite cobertos pelo diff (ou já em `develop`).
- [ ] Fora de escopo respeitado.
- [ ] Cada rota do bloco **Contrato HTTP** da SPEC existe e responde como descrito.

## REST e controllers

- [ ] `@RequestMapping` 1º segmento alinhado a permissão dinâmica (`EV-REST-001`).
- [ ] Escrita com `@Valid` quando o vizinho usa Bean Validation (`EV-REST-002`).
- [ ] Listagem paginada com 4 headers quando há `Pageable` (`EV-REST-003`).
- [ ] Novo `listar` com `*Filter` + `Pageable` (`EV-LST-001`, [`listagem-paginada-filtrada.md`](../../padrao/listagem-paginada-filtrada.md)).
- [ ] Sem colisão: paths fixos da feature não capturados por `/{id}` em controller ancestral (`EV-REST-006`, [`escopo-e-rest.md`](escopo-e-rest.md)).
- [ ] `@RequerModulo` coerente com o módulo da feature.
- [ ] Controller sem negócio/repository no diff (`EV-CTL-*`, [`controllers.md`](../../padrao/controllers.md)).

## DTO e validação

- [ ] Regras de negócio no service; não no controller (`EV-VAL-002`, `EV-CTL-001`).
- [ ] Whitelist nova: legado e formato persistido (`EV-VAL-004`).
- [ ] Exceções via `BusinessException` / `ResourceNotFoundException` (`EV-EXC-002`).

## Service (se o diff tocar `*Service`)

- [ ] Persistência só via `repository.*` / `repository.central.*` — sem JDBC/`EntityManager` novo no service tenant (`EV-SVC-001`, [`services.md`](../../padrao/services.md)).
- [ ] Sem `//` ou `/* */` no corpo do método → **Importante** (`EV-SVC-003`, [`codigo-javadoc-comentarios.md`](../importante/codigo-javadoc-comentarios.md)).
- [ ] Método/classe pública nova com JavaDoc `/**` → senão **Importante** (`EV-SVC-002`).
- [ ] JavaDoc existente mas incompleto → **Melhoria / Ajuste** (`@param`, resumo, `@since`/`@author`).
- [ ] Sem métodos mortos no diff (`EV-SVC-004`).

## Multi-tenant

- [ ] Leitura/escrita com `TenantContextService` e filtro `idOrganizacao` no repository (`EV-MTN-*`).
- [ ] Nenhum dado de outra organização no fluxo alterado.

## Persistência (se houver migration no diff)

- [ ] Migration nova; não reescrever `V*` aplicada.
- [ ] Dados e integridade (`EV-PER-006`): SQL não quebra startup (Flyway/`validate`); NOT NULL/FK/UK/CHECK com backfill ou default; sem DROP/TRUNCATE de negócio sem plano — [`banco.md`](../../padrao/banco.md).
- [ ] Tríade: SQL ↔ entity ↔ DTO/`validar()`.
- [ ] DDL alinhada a [`banco.md`](../../padrao/banco.md) (pasta tenant/central, `id_organizacao`, sem editar `V*` antigo).
- [ ] Colunas e campos novos em português com prefixos (`EV-NOM-003`, [`nomenclatura-portugues.md`](../../padrao/nomenclatura-portugues.md)).
- [ ] Permissão central só se escopo incluir `db/central` (`docs/migrations-permissoes.md`).

## Testes

- [ ] `mvn test` nas classes de teste tocadas pelo diff.
- [ ] Records/DTOs usados em testes atualizados (compilação).

## Consumidor da API (auth / erros / validação)

- [ ] **Primeiro:** [`critico/consumidor-api.md`](../critico/consumidor-api.md) + [`importante/consumidor-api.md`](../importante/consumidor-api.md) — loop login, tenant, contrato, 401/403, vazamento → **Crítico** / **Importante**.
- [ ] **Depois:** [`melhoria-ajuste/consumidor-api.md`](../melhoria-ajuste/consumidor-api.md) — polish → **Melhoria / Ajuste** só se o fluxo conclui.

## Encerramento

- [ ] Achados só com evidência (regra + arquivo + entrada → falha + impacto).
- [ ] Veredito: APROVÁVEL (Crítico e Importante = Nenhum.) ou NÃO APROVÁVEL (item em Crítico ou Importante). **Melhoria / Ajuste** não altera a Conclusão.
