# Listagem: paginação e filtragem

**Regra geral:** qualquer operação **`listar`** (ou GET que devolve **coleção** de recursos de negócio) deve oferecer **filtro** + **paginação**, salvo exceção explícita na SPEC ou contrato legado documentado.

Validador: `EV-LST-*` (`.cursor/rules/ev-listagem.mdc`). HTTP: `EV-REST-003`, `EV-REST-005`. Filtro DTO: [`dtos.md`](dtos.md). Controller: [`controllers.md`](controllers.md).

---

## Contrato padrão (cadastros e grids)

### Service

```java
@Transactional(readOnly = true)
public Page<EntidadeResponse> listar(EntidadeFilter filter, Pageable pageable) {
    Long idOrganizacao = tenantContextService.idOrganizacaoObrigatoria();
    Specification<Entidade> tenantSpec = ...;
    Specification<Entidade> filterSpec = GenericSpecificationBuilder.byFilter(filter);
    return repository.findAll(tenantSpec.and(filterSpec), pageable).map(mapper::toResponse);
}
```

- Retorno: **`Page<XxxResponse>`**, não `List<>` para listagem principal.
- Sempre escopo de **tenant** na specification/repository.
- `GenericSpecificationBuilder.byFilter(filter)` quando o filtro usa `@FilterEquals` / `@FilterLike` / `@FilterSearch`.

### DTO de filtro

`record XxxFilter` no pacote `dto.<modulo>` — ver `EntidadeFilter`, `BancoFilter`.

| Anotação | Uso |
|----------|-----|
| `@FilterEquals` | Igualdade exata (`flAtivo`, `idEntidade`) |
| `@FilterLike` | Contém / like (`nmRazaoSocial`) |
| `@FilterSearch` | Busca textual em vários campos (`pesquisa`) |

Campo `pesquisa` é o padrão do repo para “busca rápida” na listagem.

### Controller

```java
@GetMapping
public ResponseEntity<ApiResponseDTO<List<EntidadeResponse>>> listar(
        @ParameterObject EntidadeFilter filter,
        @ParameterObject @PageableDefault(size = 20, sort = "idEntidade") Pageable pageable) {

    Page<EntidadeResponse> page = service.listar(filter, pageable);

    return ResponseEntity.ok()
            .header("X-Total-Count", String.valueOf(page.getTotalElements()))
            .header("X-Page", String.valueOf(page.getNumber()))
            .header("X-Page-Size", String.valueOf(page.getSize()))
            .header("X-Total-Pages", String.valueOf(page.getTotalPages()))
            .body(new ApiResponseDTO<>("Operação realizada com sucesso", page.getContent()));
}
```

- `@ParameterObject` no **filter** e no **pageable** quando o vizinho do módulo usa (`EV-REST-005`).
- `@PageableDefault`: tamanho e `sort` coerentes com a tela (ex.: `dtVencimento` em contas).
- Quatro headers obrigatórios com `Pageable` (`EV-REST-003`).
- Body: `page.getContent()` dentro do envelope do módulo.

### Export

`GET …/export` pode usar `service.listar(filter, Pageable.unpaged()).getContent()` — export é caso especial; a listagem **interativa** continua paginada.

---

## Quando o diff traz `listar` sem paginação/filtro

| Situação no diff | Ação |
|------------------|------|
| Novo `listar` retornando `List<>` ou GET coleção sem `Pageable` | **Importante** (`EV-LST-001`): propor `XxxFilter` + `Page<>` + headers, alinhado ao vizinho (`BancoService`, `EntidadeService`). |
| `listar` sem `*Filter` mas módulo vizinho tem filtro | **Importante** (`EV-LST-002`): incluir filtro mínimo (`pesquisa`, `flAtivo`, FK do pai). |
| Endpoint combo/autocomplete (`listarAtivas`, poucos registros fixos) | Aceitável se volume for **pequeno e estável**; registrar na SPEC ou JavaDoc do service o motivo. |
| Sub-rota filha (`…/{id}/pagamentos`) | Preferir paginação se a aba for grid; lista completa só com justificativa na SPEC (volume limitado). |
| Catálogo nacional (estados, domínio fechado) | Legado aceito; novos cadastros tenant não usam esse atalho. |

O validador **sugere** o padrão; não exige refactor de `listarAtivas()` ou `CertidaoController.listar()` fora do escopo.

---

## Nomenclatura

- Método: **`listar`** (português) — `EV-NOM-003`.
- Filtro: **`XxxFilter`**.
- Não criar `getAll`, `findAll` em service público (repository Spring Data mantém `findAll` internamente).

---

## Checklist (nova listagem)

- [ ] `XxxFilter` com campos úteis à tela + `pesquisa` quando fizer sentido.
- [ ] `Page<XxxResponse> listar(XxxFilter, Pageable)` no service.
- [ ] Specification/repository com tenant.
- [ ] Controller com `@PageableDefault` e 4 headers.
- [ ] `@ParameterObject` se o módulo vizinho usa.
- [ ] SPEC menciona query params principais se escopo ampliado.

---

## Exceções documentadas (não replicar sem SPEC)

| Exemplo | Motivo |
|---------|--------|
| `EntidadeController.listarAtivas()` | Combo; lista reduzida |
| `EntidadeClienteSuperiorService.listar(idEntidade)` | Coleção sob pai (evoluir para página se crescer) |
| `ContaPagarService.listarPagamentos` | Aba filha; hoje lista integral |
| `CertidaoController.listar()` | Legado sem filtro |
| `EstadoController` com `Map` query | Legado; preferir `EstadoFilter` em refactor |

---

## Vizinhos

| Camada | Referência |
|--------|------------|
| Completo | `EntidadeController.listar`, `EntidadeService.listar`, `EntidadeFilter` |
| Financeiro | `ContaPagarController.listar`, `ContaPagarFilter` |
| Central | `CentralUsuarioSegurancaAdminService.listar` + filter |
| Padrão C listagem enxuta | [`colecao-filha-vinculada-pai.md`](colecao-filha-vinculada-pai.md) |
