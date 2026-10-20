# Padrão de controllers

Camada **HTTP**: rota, status, headers, validação de formato do body (`@Valid`). **Toda regra de negócio passa pelo service** — o controller não decide invariantes de domínio, tenant, duplicidade, estado do agregado nem acesso a dados.

Arquitetura: `.cursor/rules/architecture.mdc` (`EV-ARC-003`). Validador: `EV-CTL-*` em `.cursor/rules/ev-controllers.mdc`. REST/envelope: [`dtos.md`](dtos.md), `.cursor/rules/rest-api.mdc`.

Negócio: [`services.md`](services.md). Nomes em português nos métodos: [`nomenclatura-portugues.md`](nomenclatura-portugues.md).

---

## Fluxo obrigatório

```
Cliente  →  Controller  →  Service  →  Repository / outros services
                ↑
           só HTTP + @Valid
```

Cada handler público deve **delegar** a um método de `*Service` (ou `GenericExportService` só para montagem de arquivo de exportação). O controller **não** contorna o service chamando repository, mapper “de negócio” ou provider direto para persistir/consultar domínio.

---

## O que o controller faz

| Permitido | Exemplo |
|-----------|---------|
| `@GetMapping` / `@PostMapping` / … e `@RequestMapping` | `EntidadeController` |
| `@RequerModulo`, `@PreAuthorize` quando o vizinho usa | `BancoController.sincronizarBrasilApi` |
| `@Valid @RequestBody` / `@ParameterObject` | `criar(@Valid EntidadeRequest)` |
| `ResponseEntity` + `HttpStatus` + headers de paginação | `X-Total-Count`, … — ver [`listagem-paginada-filtrada.md`](listagem-paginada-filtrada.md) |
| `ApiResponseDTO` ou DTO direto conforme o módulo | [`dtos.md`](dtos.md) |
| Chamar **um** método de service por operação de negócio | `service.buscarPorId(id)` |
| Export: colunas e rótulos de planilha + `GenericExportService` | `exportar` em `BancoController` |
| Helper **privado** só de apresentação HTTP (ex.: mapa de filtros para PDF/Excel) | `filtrosParaExibicao` |

---

## O que o controller não faz

| Proibido em código novo | Onde deve ficar |
|-------------------------|-----------------|
| Injetar `*Repository`, `EntityManager`, `JdbcTemplate` | Service |
| `@Transactional` | Service (`EV-TXN-003`) |
| `BusinessException`, `ConflictException`, `ResourceNotFoundException` por regra de domínio | Service |
| `if`/`switch` que valida negócio (pareamento de arquivos, ciclo, saldo, status) | Service |
| `TenantContextService` para decidir regra | Service |
| Montar/alterar entity JPA | Service + mapper |
| Lógica de negócio “rápida” no controller | Service (sem exceção por tamanho) |

**Legado:** `ContratoImportacaoController` lança `BusinessException` no controller — **não replicar**; mover validação para service em refactors.

---

## Forma da classe

Pacote: `com.esimples_api.controller` (central: `controller.sistema.*`).

```java
@RequerModulo("cadastros")
@RestController
@RequestMapping("/entidades")
@AllArgsConstructor
public class EntidadeController {

    private final EntidadeService service;
    private final GenericExportService exportService;

    @GetMapping("/{id}")
    public ResponseEntity<EntidadeResponse> buscarPorId(@PathVariable Long id) {
        return ResponseEntity.ok(service.buscarPorId(id));
    }
}
```

- Injeção: services do domínio (+ `GenericExportService` se houver export).
- Métodos em **português** (`listar`, `criar`, `buscarPorId`) — `EV-NOM-003`.
- Um endpoint = uma responsabilidade HTTP clara; path fixo antes de `/{id}` quando necessário (`EV-REST-006`).

---

## Padrão de método

1. Receber parâmetros de rota, query e body já tipados (DTO/Filter).
2. Opcional: `@Valid` no body (formato/obrigatoriedade — não substitui negócio no service).
3. Chamar service: `var resultado = service.metodo(...)`.
4. Montar `ResponseEntity` (status, headers, body).

Sem comentários no corpo; sem blocos de negócio entre a chamada e o retorno.

Validação que depende de **estado persistido** ou **outras entidades** (ex.: `validarRemocaoSubcategoria`) → método no **service**, controller só expõe a rota:

```java
@GetMapping("/{id}/subcategorias/{idEntidadeSubcategoria}/validar-remocao")
public ResponseEntity<Void> validarRemocaoSubcategoria(...) {
    service.validarRemocaoSubcategoria(id, idEntidadeSubcategoria);
    return ResponseEntity.noContent().build();
}
```

---

## Sub-recursos e coleções filhas

- Rotas aninhadas (`/entidades/{id}/…`, `/conta-pagar/{id}/pagamentos`) delegam ao **service** do agregado ou ao service do filho — nunca repository no controller.
- Ordem de paths e colisão com `/{id}`: [`colecao-filha-vinculada-pai.md`](colecao-filha-vinculada-pai.md), `docs/validador/processo/escopo-e-rest.md`.

---

## Exportação (`/export`)

Padrão do repo: controller chama `service.listar(..., Pageable.unpaged())`, define colunas legíveis e `exportService.exportar`. Isso é **apresentação**, não regra de negócio. Filtros de negócio continuam no service/repository via `Filter`.

---

## Checklist (endpoint novo)

- [ ] Handler chama apenas service (+ export infra se aplicável).
- [ ] Sem repository/EM/JDBC no controller.
- [ ] Sem exceção de negócio lançada no controller.
- [ ] `@Valid` em escrita com DTO constraint; negócio no service (`EV-VAL-002`).
- [ ] Contrato HTTP alinhado ao vizinho (envelope, headers, status).
- [ ] `@RequerModulo` coerente com permissão do 1º segmento (`EV-REST-001`).

---

## Vizinhos

| Caso | Classe |
|------|--------|
| CRUD fino + listagem paginada | `EntidadeController`, `BancoController` |
| Financeiro + sub-rota + idempotency | `ContaPagarController` |
| Anti-padrão (negócio no controller) | `ContratoImportacaoController` (legado) |
