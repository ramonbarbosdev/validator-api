# Padrão de DTOs (API)

Contrato JSON entre cliente e controllers. **Entity JPA não entra no controller** (`EV-DTO-001`).

Regras Cursor: `.cursor/rules/rest-api.mdc` (`EV-REST-*`, `EV-DTO-*`), `.cursor/rules/validation.mdc` (`EV-VAL-*`). Idioma e prefixos: [`nomenclatura-portugues.md`](nomenclatura-portugues.md). Colunas SQL: [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md).

---

## Panorama no repositório (estado atual)

| Aspecto | Padrão dominante | Exceções legadas |
|---------|------------------|------------------|
| Tipo Java | `public record` para Request/Response/Filter | Classe Lombok: `CatalogoRequest`, `GrupoRequest`, `EntidadeStatusRequest`, alguns `Central*RequestDTO` |
| Pacote | `com.esimples_api.dto.<modulo>` (pasta minúscula) | `*RequestDTO` na raiz `dto` (auth, admin) |
| Validação de campo | Jakarta (`@NotNull`, `@Size`, …) + `@Valid` no controller | `validar()` em **2** requests: `CatalogoRequest`, `LancamentoFinanceiroRequest` |
| Resposta HTTP | **Misto no mesmo controller** | Ver seção [Envelope](#envelope-http) |
| Listagem | `ApiResponseDTO<List<T>>` + 4 headers de página | GET `/{id}` e POST/PUT costumam retornar `T` direto |
| Agregados SQL | Interface `*Projection` no `dto` | Consumida só no mapper/service |

Código novo: seguir a coluna **Padrão dominante**; não copiar legado sem motivo na SPEC.

---

## Organização

```
com.esimples_api.dto
├── ApiResponseDTO, ApiErrorResponse          # envelope / erro global
├── <modulo>/                                 # ex.: contapagar, entidade, banco
│   ├── XxxRequest, XxxResponse
│   ├── XxxFilter
│   ├── XxxFilhoRequest / XxxFilhoResponse
│   └── *Projection (consulta interna)
├── provider.*.dto                            # resposta de API externa
└── export.ExportRequest                      # exportação (fora de dto/)
```

Admin central: pacotes `plano`, `solicitacao`, `sistema` — muitos tipos com sufixo **`DTO`** (`CentralPlanoRequestDTO`). Tenant novo: **`Request` / `Response`** sem `DTO`.

---

## Sufixos de classe

| Sufixo | Quando usar |
|--------|-------------|
| `Request` | Body POST, PUT, PATCH com JSON |
| `Response` | Corpo de sucesso (detalhe, item de lista, sub-recurso) |
| `Filter` | Query string da listagem (`BancoFilter`, `ContaPagarFilter`) |
| `StatusRequest` | PATCH com body mínimo de ativação (quando não for `@RequestParam`) |
| `ResumoResponse` | FK “expandida” enxuta dentro de outro response (`CatalogoResumoResponse`) |
| `HistoricoResponse` | Linha de auditoria/evento (`ContaPagarHistoricoResponse`) |
| `Sugestao*Response` | Pré-preenchimento (`SugestaoContaPagarResponse`) |
| `*Projection` | Projeção Spring Data; **não** serializar como contrato público |
| `*ConsultaResponse` | Relatório/consulta composta (`ExtratoFinanceiroConsultaResponse`) |

---

## Record vs classe

### Preferência: `record` (`EV-DTO-002`)

Imutável, alinhado à maioria dos módulos financeiros e cadastros.

```java
public record BancoRequest(
    @NotBlank(message = "O código do COMPE é obrigatório")
    String cdCompe,
    @NotNull(message = "O Status do banco é obrigatório")
    Boolean flAtivo,
    LocalDateTime dtDesativacao
) {}
```

Referências: `BancoRequest`, `ContaPagarRequest`, `EntidadeRequest`, `ContaPagarPagamentoRequest`.

### Classe (só quando necessário)

- Request com `validar()` que faz `trim` ou normaliza campos antes do service (`CatalogoRequest`).
- PATCH/status antigos com Lombok (`EntidadeStatusRequest`).

Em feature **nova**, usar record; regras condicionais complexas → service (`BusinessException`) ou `validar()` compacto no record.

---

## Nomes dos campos no JSON

Espelhar o modelo persistido em **camelCase**:

| Prefixo | Exemplo JSON |
|---------|----------------|
| `id` | `idContaPagar`, `idEntidade` |
| `nm` | `nmRazaoSocial`, `nmBanco` |
| `fl` | `flAtivo`, `flFornecedor` |
| `dt` | `dtVencimento`, `dtDesativacao` |
| `vl` | `vlPagar`, `vlPago` |
| `tp` | `tpSituacao`, `tpPessoa` |
| `cd` | `cdCompe`, `cdBarras` |
| `ds` | `dsObservacao`, `dsHistorico` |
| `nu` | `nuDocumento`, `nuParcela` |

- **Request:** FK como `Long id…`.
- **Response de detalhe:** FK + descrições preenchidas no **mapper** (`nmRazaoSocial`, `dsSubCategoria`).
- **Enums** de domínio no tipo Java (`SituacaoContas`, `TipoCatalogo`).

Legado: `EntidadeStatusRequest` usa `ativo` em vez de `flAtivo`. Novos endpoints de status: preferir `flAtivo` e `dtDesativacao` quando a tabela tiver esses campos.

---

## Validação em camadas

```
Controller @Valid  →  (opcional) request.validar()  →  Service (tenant, duplicidade, domínio)
```

| Camada | Responsabilidade |
|--------|------------------|
| Bean Validation no DTO | Obrigatoriedade, tamanho, formato, `@Positive`, aninhados `@Valid` |
| `validar()` no request | Regras por combinação de campos / lista fechada difícil em anotação |
| Service | Multi-tenant, existência de FK, conflito, ciclo, invariantes de negócio (`EV-VAL-002`) |

Controller de escrita:

```java
public ResponseEntity<ContaPagarResponse> criar(@Valid @RequestBody ContaPagarRequest request)
```

Chamadas a `validar()` hoje:

| Request | Onde |
|---------|------|
| `CatalogoRequest` | `CatalogoService.criar` / `atualizar` |
| `LancamentoFinanceiroRequest` | `LancamentoFinanceiroService` |

Após `@Valid` no controller, o service chama `request.validar()` quando existir. Whitelist / valor legado na edição: `EV-VAL-004`.

Mensagens de constraint em **português** (`EV-VAL-003`).

---

## Mestre, filhos e listagem (Padrão C)

**Escrita no pai:** coleção ou objeto aninhado no `*Request` principal.

```java
public record ContaPagarRequest(
    // ... campos do título ...
    @Valid ContaPagarRetencaoRequest retencao,
    @Valid List<ContaPagarPagamentoRequest> pagamentos
) {}
```

- Filho em lista pode trazer `id…` opcional para update (`idContaPagarPagamento`).
- **Aba / sub-rota:** `ContaPagarPagamentoRequest` + `ContaPagarPagamentoResponse` em `GET/POST …/{id}/pagamentos`.

**Leitura:**

| Cenário | Mapper / endpoint |
|---------|-------------------|
| Listagem paginada | `toResponseListagem` — sem hidratar coleção pesada |
| GET `/{id}` | `toResponse` ou `toResponseComTotaisAgregados` |
| Aba filha | Lista de `*FilhoResponse` na sub-rota |

Detalhes: [`colecao-filha-vinculada-pai.md`](colecao-filha-vinculada-pai.md), [`mestre-detalhe-conta-receber.md`](mestre-detalhe-conta-receber.md).

---

## Filtros de listagem

Todo **`listar`** de grid/cadastro deve ter `XxxFilter` + paginação — [`listagem-paginada-filtrada.md`](listagem-paginada-filtrada.md) (`EV-LST-*`).

`record` + anotações em `com.esimples_api.shared`:

```java
public record BancoFilter(
    @FilterEquals Long idBanco,
    @FilterLike String nmBanco,
    @FilterEquals Boolean flAtivo,
    @FilterSearch(paths = {"nmReduzido", "nmBanco", "cdCompe"})
    String pesquisa
) {}
```

Controller: `XxxFilter` ou `@ParameterObject XxxFilter`, `Pageable`, `@PageableDefault`, headers `X-Total-Count`, `X-Page`, `X-Page-Size`, `X-Total-Pages` (`EV-REST-003`).

---

## Envelope HTTP

`ApiResponseDTO<T>`:

```json
{ "message": "Operação realizada com sucesso", "data": … }
```

**Padrão observado em cadastros/financeiro (ex. `BancoController`, `ContaPagarController`):**

| Operação | Tipo de retorno típico |
|----------|-------------------------|
| `GET` listagem (paginada) | `ApiResponseDTO<List<XxxResponse>>` + headers |
| `GET` sub-lista / sugestão / delete mensagem | `ApiResponseDTO<…>` |
| `GET /{id}`, `POST`, `PUT`, `PATCH` de recurso | **`XxxResponse` direto** (sem envelope) |

Novo endpoint: **copiar o vizinho do mesmo controller/recurso** (`EV-REST-004`). Não misturar envelope e DTO nu no mesmo fluxo sem combinar na SPEC.

---

## Mapper

Classe `@Component` `*Mapper` (ex. `ContaPagarMapper`):

| Método | Uso |
|--------|-----|
| `toResponse` | Detalhe com filhos quando o service carregou a coleção |
| `toResponseListagem` | Grid / listagem enxuta |
| `toResponseComTotaisAgregados` | Detalhe com totais via `*TotaisProjection` |
| `toResponseCriacao` | Resposta pós-POST com campos calculados só na criação |

Entity → DTO só no mapper; controller não monta response campo a campo.

---

## Checklist (feature nova)

- [ ] `dto.<modulo>/XxxRequest` e `XxxResponse` como **record** (salvo `validar()` mutável).
- [ ] Campos JSON com prefixos alinhados à migration/entity.
- [ ] `@Valid` no body de escrita; `@Valid` em listas/objetos aninhados.
- [ ] `XxxFilter` se houver listagem com filtros.
- [ ] Mapper com variantes listagem vs detalhe se a carga divergir.
- [ ] Envelope e headers iguais ao controller vizinho do módulo.
- [ ] Regra de negócio forte no service; DTO só formato e obrigatoriedade.

---

## Vizinhos por caso

| Caso | Arquivos |
|------|----------|
| CRUD record + listagem envelope | `BancoRequest`, `BancoController` |
| Financeiro mestre + filhos | `ContaPagarRequest`, `ContaPagarMapper`, `ContaPagarController` |
| Cadastro rico (listas aninhadas) | `EntidadeRequest` |
| `validar()` + fiscal | `CatalogoRequest`, `CatalogoService` |
| Resumo embutido | `CatalogoResumoResponse` |
| Projeção de totais | `ContaPagarPagamentosTotaisProjection` |
| Histórico | `ContaPagarHistoricoResponse` |
| PATCH status query param | `BancoController.alterarStatus(@RequestParam boolean ativo)` |
