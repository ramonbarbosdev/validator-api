# Padrão de banco de dados (DDL / Flyway / JPA)

Normas para **migrations**, **schemas**, **tenant**, **constraints** e **entity**. Colunas: [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md) · PT: [`nomenclatura-portugues.md`](nomenclatura-portugues.md).

Validador: `.cursor/rules/persistence.mdc`, `ev-ddl-nomenclatura.mdc`, `multi-tenant.mdc`.

**No projeto alvo:** manter `docs/arquitetura-banco-atual.md` (mapa de schemas/tabelas) e `docs/migrations-permissoes.md` se houver banco central — o validador usa como referência, não exige doc atualizada (`EV-ESP-003`).

---

## Onde vive cada DDL

| Destino | Caminho típico (Spring) | Uso |
|---------|-------------------------|-----|
| **Tenant** | `src/main/resources/db/migration/` | Negócio isolado por organização |
| **Central** | `src/main/resources/db/central/` | Catálogo global, auth, permissões |

`EV-PER-001` / `EV-PER-002`: não misturar responsabilidades tenant ↔ central.

---

## Flyway

- `V{N}__descricao.sql` — uma versão por arquivo (`EV-PER-004`).
- **Nunca** alterar/apagar migration já aplicada; correção = novo `V*`.
- Hibernate `validate`: DDL só via Flyway.

---

## Prioridade: dados existentes e integridade (`EV-PER-006`)

O padrão do projeto coloca **dados já persistidos** e **integridade** acima de atalhos de DDL. A migration **não pode quebrar a aplicação** na subida nem deixar o banco em estado inconsistente com o que o código espera.

### Por que importa

- Flyway roda no **startup**: SQL que falha → deploy parado (tenant e/ou central).
- Após o Flyway, Hibernate **`validate`** compara entity com schema; desalinhamento também impede subida.
- Ambientes com **dados reais** não podem ser tratados como banco vazio.

### Regras de revisão (diff com `V*` novo)

| Situação no SQL | Julgamento típico |
|-----------------|-------------------|
| `ADD COLUMN ... NOT NULL` sem `DEFAULT` e sem `UPDATE`/backfill prévio em linhas existentes | **Crítico** — falha em tabela populada |
| `DROP` / `TRUNCATE` / `DELETE` em massa em dado de negócio sem plano na SPEC/atividade | **Crítico** |
| FK, UK ou `CHECK` que rejeita registros já existentes sem normalização antes | **Crítico** ou **Importante** (com evidência de órfãos) |
| Mudança de tipo / `RENAME` sem conversão e sem entity/código no núcleo da atividade | **Crítico** se quebra subida ou leitura |
| DDL só em ambiente “verde” (assume tabela vazia) em módulo já em produção | **Importante** ou **Crítico** conforme impacto |

### Padrão preferido (expand-first)

1. **Adicionar** coluna/tabela (nullable ou com `DEFAULT` seguro para legado).
2. **Backfill** na mesma migration ou em `V*` seguinte (`UPDATE … WHERE …`).
3. **Restringir** depois: `SET NOT NULL`, FK, UK, `CHECK` — quando não houver linha violadora.
4. Manter **tríade** migration ↔ entity ↔ validação no fluxo de escrita alinhada ao schema **final**.

### Integridade

- FK e UK devem refletir relações reais do domínio; não “fechar” constraint em dados sujos sem etapa de correção.
- Tenant: não enfraquecer `id_organizacao` / isolamento por organização em nome de DDL mais simples (`EV-MTN-*` prevalece).

Detalhe de nomenclatura e tríade: seções abaixo e [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md).

---

## Schemas

- PostgreSQL com **schemas por módulo** (`public`, `financeiro`, `contrato`, …) conforme o projeto.
- SQL qualificado: `schema.tabela`; entity com `@Table(schema = "...", name = "...")`.
- Novo objeto: **mesmo schema** do vizinho do módulo (SPEC ou tabela análoga).

---

## Multi-tenant

- `id_organizacao NOT NULL` + índice nas tabelas de negócio tenant.
- Entity base tipo `TenantEntity` + filtro no repository/service (`EV-MTN-*`).
- Referência a catálogo central por ID: validação no service, sem FK entre bancos (`EV-MTN-004`).

---

## Tabelas, constraints, índices

- Tabela `snake_case`; colunas com prefixos (`id_`, `nm_`, `fl_`, `dt_`, `vl_`, `tp_`, …).
- `fk_*`, `uk_*`, `ck_*`, `idx_*`; mensagens em `ConstraintMessageMap` quando aplicável.
- SPEC literal de nomes → `EV-DDL-001`.

---

## Tríade

1. Migration SQL  
2. `@Column` / entity  
3. DTO + service  

---

## Transações

Service: `@Transactional`; central: `centralTransactionManager`. Sem TX no controller.

---

## Checklist (diff com migration)

- [ ] `EV-PER-006`: subida segura (Flyway + `validate`); backfill/default antes de NOT NULL/FK/UK restritivos
- [ ] `V*` novo no pasta certa (tenant vs central)
- [ ] `id_organizacao` + índice se tenant
- [ ] Entity alinhada; tríade com DTO
- [ ] Sem edição de `V*` legado no diff

---

## Stack e-Simples

Exemplos concretos de schema `financeiro` e migrations: instalar overlay `java-spring-esimples` e ver `docs/arquitetura-banco-atual.md` no projeto e-Simples.
