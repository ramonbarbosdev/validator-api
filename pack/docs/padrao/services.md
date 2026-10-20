# Padrão de services

Camada de **regra de negócio** e orquestração. Controller só HTTP — ver [`controllers.md`](controllers.md) (`EV-CTL-*`, `EV-ARC-003`). Persistência e transação: `.cursor/rules/persistence.mdc` (`EV-TXN-*`). Arquitetura: `.cursor/rules/architecture.mdc`.

Regras do validador: `EV-SVC-*` em `.cursor/rules/ev-services.mdc`. Nomes em português: [`nomenclatura-portugues.md`](nomenclatura-portugues.md) (`EV-NOM-003`).

---

## Responsabilidade

| Faz no service | Não faz no service |
|----------------|-------------------|
| Validar tenant (`TenantContextService`) | SQL/JPQL/`EntityManager`/`JdbcTemplate` |
| Chamar `*Repository` para ler/gravar | Montar JSON de resposta HTTP |
| Chamar `*Mapper` entity ↔ DTO | Anotações de rota ou `@Valid` no body |
| Orquestrar outros `*Service` do domínio | Acesso direto a tabela sem repository |
| `BusinessException`, `ResourceNotFoundException`, … | Comentários `//` ou `/* */` **dentro** do corpo do método |
| Invocar `request.validar()` quando o DTO tiver | Métodos mortos (sem chamada no projeto) |

Consultas e comandos de banco ficam em **`repository.*`** (tenant) ou **`repository.central.*`** (central, com `centralTransactionManager`). Se a query não existe, **criar método no repository** (ou `*RepositoryCustom` + impl), não abrir JDBC no service.

---

## Persistência (regra de ouro)

```
Service  →  Repository  →  banco
```

- Tenant: `com.esimples_api.repository.*`, `@Transactional` padrão.
- Central: `repository.central.*`, `@Transactional(transactionManager = "centralTransactionManager")`.
- Leitura: `@Transactional(readOnly = true)` nos métodos públicos de consulta (`EV-TXN-001`).

**Código novo (tenant de negócio):** proibido injetar `EntityManager`, `JdbcTemplate`, `NamedParameterJdbcTemplate` no service do módulo.

**Legado (não copiar):** alguns serviços centrais/auth ainda usam JDBC direto (`LogAtividadeService`, `CentralPlatformService`, `AuthRefreshTokenService`, `AuditoriaContratoService` com `EntityManager`). Novas features e refactors devem extrair acesso para repository.

---

## Estrutura da classe

Pacote: `com.esimples_api.service` (central admin: prefixo `Central` quando aplicável).

```java
@Slf4j
@Service
@AllArgsConstructor
public class BancoService {

    private final BancoRepository bancoRepository;
    private final BancoMapper bancoMapper;
    private final TenantContextService tenantContextService;

    // métodos públicos → JavaDoc
    // helpers private → sem comentário inline; nome claro ou JavaDoc se a regra for obscura
}
```

- Injeção por construtor (`@AllArgsConstructor` ou construtor explícito — `EV-ARC-006`).
- Dependências: repositories do domínio, mappers, `TenantContextService`, outros services, **providers** externos (`provider.*`), regras em `domain.*` quando existirem.
- Métodos `private` para duplicidade, normalização, montagem de `Specification` — **sem** comentários no meio do algoritmo.

Vizinho típico tenant: `BancoService`, `CatalogoService`. Vizinho financeiro complexo: `ContaPagarService` (ainda sem JavaDoc em massa — padrão vale para **código novo e alterado**).

---

## JavaDoc (obrigatório)

**Classe:** resumo do agregado/recurso que o service governa.

**Métodos públicos:** o que faz, pré-condições relevantes (tenant, idempotência), efeitos colaterais (histórico, fila), exceções esperadas.

Formato alinhado ao restante do projeto (ex. módulo auth):

```java
/**
 * Sincroniza a coleção de pagamentos do request com o persistido na conta.
 * Exige organização do {@link TenantContextService} e conta não cancelada.
 *
 * @param idContaPagar identificador da conta no tenant atual
 * @param pagamentos   lista do body (pode ser vazia para remover todos)
 * @author Ramon Barbosa Souza
 * @since 19/10/2026
 */
@Transactional
public void sincronizarPagamentos(Long idContaPagar, List<ContaPagarPagamentoRequest> pagamentos) {
    ...
}
```

- `@author` e `@since` nos métodos públicos **novos** ou quando o método for criado/alterado de forma relevante na branch.
- `{@link}` para tipos de exceção ou services citados.
- **Proibido** usar comentário de linha/bloco no interior do método para “documentar”; se precisar explicar, extrair método privado com nome expressivo ou JavaDoc no método privado.

---

## Comentários

| Permitido | Proibido |
|-----------|----------|
| JavaDoc `/** … */` antes de classe, record interno, método | `// …` dentro de método |
| `/** … */` em constantes `private static final` se o valor for opaco | Blocos `/* … */` explicando passos no meio do fluxo |
| Anotações (`@Transactional`, etc.) | Comentários “TODO” sem issue — usar issue/SPEC |

---

## Métodos sem utilização

- Não deixar `public` ou `private` sem referência no repositório (IDE / compilador / busca).
- Antes de merge: remover código morto introduzido no diff; não manter “para uso futuro”.
- Se o endpoint foi removido, remover o método de service correspondente.

---

## Fluxo típico (CRUD tenant)

1. Obter `idOrganizacao` via `tenantContextService.idOrganizacaoObrigatoria()`.
2. Montar `Specification` ou usar `findById…` do repository com escopo de org.
3. Validar negócio (duplicidade, estado, FKs) → exceções do pacote `exception`.
4. `mapper.toEntity` / alterar entity / `repository.save`.
5. Retornar `mapper.toResponse` (ou `Page` mapeada).

Escrita em coleção filha: ver [`colecao-filha-vinculada-pai.md`](colecao-filha-vinculada-pai.md). DTOs: [`dtos.md`](dtos.md).

---

## Checklist (service novo ou refactor)

- [ ] Classe e métodos públicos com JavaDoc (`@author`, `@since` na alteração).
- [ ] Nenhum `EntityManager` / `JdbcTemplate` no service tenant.
- [ ] Queries novas no repository (ou extensão), não no service.
- [ ] `@Transactional` / `readOnly` coerentes com leitura vs escrita.
- [ ] Sem comentários dentro de métodos.
- [ ] Sem métodos órfãos.
- [ ] Negócio no service; formato no DTO; persistência no repository.

---

## Vizinhos

| Caso | Classe |
|------|--------|
| CRUD + Specification + tenant | `BancoService` |
| `validar()` no DTO + domínio | `CatalogoService` |
| Mestre–detalhe + histórico | `ContaPagarService` |
| JavaDoc + central JDBC (legado) | `AuthRefreshTokenService` |
| Central com repository | `CentralTipoDocumentoFinanceiroService` (quando existir no módulo) |
