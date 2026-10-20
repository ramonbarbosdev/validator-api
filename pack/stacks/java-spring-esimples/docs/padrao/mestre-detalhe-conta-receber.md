# Padrão mestre–detalhe (referência: Conta a receber + Recebimentos)

**Use este documento como modelo** ao separar listagem, cabeçalho do formulário e aba de filhos em outros módulos (Entidade, Colaborador, etc.).

**Padrão C** (listagem) e filho agregado: [`colecao-filha-vinculada-pai.md`](colecao-filha-vinculada-pai.md) · manifesto `listagem_c`: [`carga-faixa-manifest.json`](carga-faixa-manifest.json).

Espelho no financeiro: **Conta a pagar** (`ContaPagarService`, `GET /conta-pagar/{id}/pagamentos`).

---

## Ideia em uma frase

| Camada | O que o front chama | O que vem no JSON |
|--------|---------------------|-------------------|
| **Listagem** | `GET /conta-receber` (paginado) | Só **cabeçalho** do título; **sem** linhas de recebimento |
| **Mestre (formulário)** | `GET /conta-receber/{id}` | Cabeçalho + **totais** (saldo, somas); `recebimentos[]` **sempre vazio** |
| **Detalhe (aba)** | `GET /conta-receber/{id}/recebimentos` | Só a **lista** de recebimentos |
| **Escrita** | `POST` / `PUT /conta-receber/{id}` | Body **único** com `recebimentos[]` no request (como hoje) |

Leitura **dividida**; gravação **junto** no pai.

---

## Fluxo do front (tela do título)

```text
1. Grid                    → GET /conta-receber?page=…     (leve)
2. Abrir título            → GET /conta-receber/{id}         (cabeçalho + totais)
3. Aba Recebimentos        → GET /conta-receber/{id}/recebimentos
4. Salvar formulário       → PUT /conta-receber/{id}       (request com recebimentos[])
```

Não depender do `GET /{id}` para popular a grid da aba.

---

## Contrato HTTP (mestre)

| Método | Rota | Response |
|--------|------|----------|
| `GET` | `/conta-receber` | `Page` → `ContaReceberResponse` via **`toResponseListagem`** |
| `GET` | `/conta-receber/{id}` | `ContaReceberResponse` via **`toResponseComTotaisAgregados`** |
| `GET` | `/conta-receber/{id}/recebimentos` | Página de `ContaReceberRecebimentoResponse` (headers `X-Total-*`; query `page`, `size`, `sort` + `ContaReceberRecebimentoFilter`) |
| `POST` | `/conta-receber` | `ContaReceberRequest` (inclui `recebimentos`) → `toResponse` após salvar |
| `PUT` | `/conta-receber/{id}` | Idem |
| `PATCH` | `/conta-receber/{id}/recebimentos/{idRecebimento}/…` | Ações pontuais no filho; permissão no **pai** |

Rotas de **histórico**, **estorno** e **export** seguem o mesmo recurso `/conta-receber`.

---

## O que cada response contém

### Listagem (`toResponseListagem`)

- Campos do título (cliente, valores, situação, retenção resumida, etc.).
- Totais de recebimento **não** calculados na página (evita N+1).
- `recebimentos`: lista **vazia** (campo existe no DTO, sem itens).

### Mestre `GET /{id}` (`toResponseComTotaisAgregados`)

- Mesmo cabeçalho do DTO.
- `vlTotalRecebido`, `vlTotalDescontos`, `vlTotalJurosMultas`, `vlSaldoReceber` preenchidos via **agregação SQL** (`SUM` na tabela filha).
- `recebimentos[]`: **vazio** de propósito.

### Aba (`listarRecebimentos`)

- Um item por linha de `conta_receber_recebimento`, com conta/banco da baixa.
- Ordenação padrão: `dtRecebimento`, `idContaReceberRecebimento` (`@PageableDefault`).
- Filtros opcionais no record `ContaReceberRecebimentoFilter` (mesmas anotações da listagem mestre: `@FilterEquals`, `@FilterDateRange`, …).

### Após `POST`/`PUT` (`toResponse` com coleção em memória)

- Response completo do **detalhe de escrita**: totais calculados nos recebimentos já anexados à entidade salva; `recebimentos[]` no JSON continua **vazio** (front recarrega a aba se precisar).

---

## Onde está no código (mapa)

| Responsabilidade | Arquivo |
|------------------|---------|
| Rotas | `ContaReceberController` |
| Orquestração | `ContaReceberService` |
| Listagem | `listar` → `ContaReceberMapper.toResponseListagem` |
| Mestre | `buscarPorId` → `somarTotaisRecebimentos` + `toResponseComTotaisAgregados` |
| Aba | `listarRecebimentos` → `GenericSpecificationBuilder.byFilterUnderParent` + `ContaReceberRecebimentoRepository.findAll` |
| Escrita filhos | `sincronizarRecebimentos` (no `PUT`/`POST`) |
| Mutação que precisa da coleção | `buscarEntidadeComRecebimentos` → `buscarComRecebimentosPorId` |
| Leitura leve do pai | `buscarEntidade` → `findByIdContaReceberAndOrganizacaoIdOrganizacao` (**sem** graph de recebimentos) |

### Repositório do pai (`ContaReceberRepository`)

| Método | Uso |
|--------|-----|
| `findAll` + graph | Listagem: entidade, subcategoria, conta do **título** — **sem** `recebimentos` |
| `findByIdContaReceberAndOrganizacaoIdOrganizacao` | `GET /{id}` cabeçalho |
| `buscarComRecebimentosPorId` | Atualizar, estornar, editar baixa (precisa da coleção na memória) |
| `somarTotaisRecebimentosPorConta` | Totais do `GET /{id}` |
| `existsRecebimentoPorConta` | Regra de exclusão sem carregar filhos |

### Repositório do filho (somente listagem dinâmica)

| Artefato | Uso |
|----------|-----|
| `ContaReceberRecebimentoRepository` | `JpaSpecificationExecutor` + `findAll(spec, pageable)` na aba |
| `ContaReceberRecebimentoFilter` | Query params da aba (OpenAPI via `@ParameterObject`) |

Agregações (`SUM`, `exists`) e `buscarComRecebimentosPorId` **permanecem no repositório do pai**. O repo do filho existe só quando a aba precisa de **filtro + paginação** genéricos.

---

## Paginação e filtro em sub-rotas (padrão reutilizável)

Mesma “cola” da listagem mestre, com escopo fixo do pai:

1. **HTTP:** `@ParameterObject XxxFilhoFilter` + `@PageableDefault` + `PaginatedHttpResponse.ok(page, content, message)` (headers `X-Total-Count`, `X-Page`, …).
2. **Service:** validar pai existe no tenant → `Specification` = `byFilterUnderParent(filter, "pai.idPai", idPai, idOrganizacao)` → `filhoRepository.findAll(spec, pageable).map(mapper)`.
3. **Filtro:** um **record por aba** (campos de negócio da grid); não existe filter genérico único para todos os módulos.
4. **Ordenação:** `sort` na query string; default no controller.
5. **Fetch:** evitar `JOIN FETCH` na query paginada (Hibernate + `LIMIT`); aceitar LAZY na página ou `@BatchSize` se N+1 aparecer.

Copiar para `GET /conta-pagar/{id}/pagamentos`, `GET /entidade/{id}/enderecos`, etc.: trocar entidade, `parentPath` e o record de filtro.

---

## Regras que não mudam

1. **Multi-tenant:** todo acesso filtra `idOrganizacao` do contexto.
2. **Sem controller do filho** para CRUD de grid (só rotas aninhadas no pai ou ações específicas).
3. **Request:** `ContaReceberRequest` mantém `List<ContaReceberRecebimentoRequest> recebimentos`.
4. **Permissão:** segmento `conta-receber` (filtro dinâmico + módulo financeiro).
5. **Listagem e export** seguem o **Padrão C** (payload enxuto).

---

## Checklist para replicar em outro módulo

Substitua *Recebimento* / *conta-receber* pelo seu par mestre/filho.

- [ ] `toResponseListagem` na paginação; filhos **vazios** ou omitidos no DTO de lista.
- [ ] `GET /{pai}/{id}`: totais agregados se a UI precisar; array do filho **vazio** no JSON.
- [ ] `GET /{pai}/{id}/{filhos}`: `XxxFilhoFilter` + `Pageable` + `PaginatedHttpResponse`; `byFilterUnderParent` + repo do filho com `JpaSpecificationExecutor`.
- [ ] `exists…PorConta` (ou equivalente) para regras que só perguntam “tem filho?”.
- [ ] `buscarCom…PorId` com `@Query` + `@EntityGraph` **no pai** apenas para fluxos de escrita que sincronizam a coleção.
- [ ] `POST`/`PUT`: body do pai com lista de requests do filho; `substituir*` / `sincronizar*` no service do pai.
- [ ] Atualizar [`carga-faixa-manifest.json`](carga-faixa-manifest.json) (`listagem_c: ok` quando a listagem estiver alinhada).
- [ ] Testes: `ContaReceberServiceTest` (listagem, `buscarPorId` totais, sub-rota, exclusão com `exists`).

---

## Erros comuns (evitar)

| Erro | Correção |
|------|----------|
| `listar().map(mapper::toResponse)` com filhos LAZY | Usar `toResponseListagem` |
| `GET /{id}` retornando dezenas de linhas do filho | Aba dedicada + array vazio no mestre |
| `@EntityGraph(attributePaths = "filho")` em query que retorna entidade **filha** no repo do **pai** | Usar `JOIN FETCH` na JPQL ou graph só em query que retorna o pai |
| Nome derivado `findById…ComRecebimentos…` | Spring interpreta `ComRecebimentos` como propriedade; usar `@Query` (`buscarComRecebimentosPorId`) |
| Repo do filho “só porque sim” | Repo do filho **só** para `findAll(Specification, Pageable)`; `@Query` de agregação no pai |

---

## Referência rápida — Conta a pagar

Mesma divisão: `toResponseListagem`, `toResponseComTotaisAgregados`, `GET /conta-pagar/{id}/pagamentos`, métodos `listarPagamentosPorConta` / `somarTotaisPagamentosPorConta` em `ContaPagarRepository`.

Próximos candidatos a alinhar: **Entidade** (cliente), **Colaborador** — hoje listagem ainda embute filhos (manifesto: `violation`).
