# Nomenclatura em português (todo o sistema)

**Regra geral:** identificadores de **negócio** em **português**. Não usar inglês em nome de **função/método**, **classe de model**, **coluna SQL** ou **campo Java/JSON** (`name`, `active`, `description`, `createdAt`, `userId`, etc.) **salvo exceção** listada abaixo ou texto literal na SPEC.

Validador: `EV-NOM-003`, `EV-NOM-004` (`.cursor/rules/project-conventions.mdc`). Colunas SQL (detalhe): [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md).

---

## O que é “identificador de negócio”

| Onde | Exemplo correto | Evitar em código novo |
|------|-----------------|------------------------|
| Coluna SQL | `nm_banco`, `fl_ativo`, `dt_criacao` | `name`, `active`, `created_at` |
| Campo entity/DTO | `nmBanco`, `flAtivo`, `dtCriacao` | `bankName`, `isActive`, `createdAt` |
| Classe `@Entity` | `ContaPagar`, `Entidade`, `Banco` | `PaymentAccount`, `Customer` |
| Método service/controller | `listar`, `criar`, `buscarPorId`, `validarDuplicidade` | `findAll`, `create`, `getById`, `validateDuplicate` |
| Método privado no service | `obterBancoDaOrganizacao`, `normalizarCompe` | `fetchBank`, `normalizeCode` |
| Enum de domínio | `SituacaoContas`, `TipoCatalogo` | `AccountStatus` (novo) |
| JSON da API | `idContaPagar`, `vlPagar` | `paymentId`, `amount` |

Pacotes Java (`com.esimples_api.service`), sufixos de camada (`Controller`, `Service`, `Repository`, `Request`, `Response`, `Mapper`, `Filter`) e anotações de framework **não** entram nesta regra — são convenção técnica Java/Spring.

---

## Prefixos (SQL e Java alinhados)

Usar os mesmos prefixos em migration, `@Column`, DTO e JSON (camelCase):

| Prefixo | Significado | Exemplos |
|---------|-------------|----------|
| `id_` / `id` | Identificador, FK | `id_banco`, `idContaPagar` |
| `nm_` / `nm` | Nome, rótulo | `nm_razao_social`, `nmRazaoSocial` |
| `ds_` / `ds` | Descrição, texto longo | `ds_observacao` |
| `fl_` / `fl` | Flag booleana | `fl_ativo`, `flFornecedor` |
| `dt_` / `dt` | Data/hora | `dt_vencimento` |
| `vl_` / `vl` | Valor monetário/numérico | `vl_pagar` |
| `tp_` / `tp` | Tipo, situação enumerada | `tp_situacao` (preferir a `tp_status` em coluna nova) |
| `cd_` / `cd` | Código | `cd_compe` |
| `nu_` / `nu` | Número documento/parcela | `nu_documento` |

Regra `id_<tudojunto>` / `nm_<tudojunto>`: [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md).

---

## Métodos

### Service e controller (públicos e privados)

Verbos e nomes em **português**, alinhados ao vizinho do módulo:

| Intenção | Padrão | Vizinho |
|----------|--------|---------|
| Listagem paginada | `listar` | `BancoService.listar` |
| Detalhe | `buscarPorId` | `BancoService.buscarPorId` |
| Inclusão | `criar` | `BancoService.criar` |
| Alteração | `atualizar` | `BancoService.atualizar` |
| Exclusão | `deletar` / `excluir` | conforme controller do módulo |
| Status | `alterarStatus` | `BancoController.alterarStatus` |
| Validação interna | `validar…`, `obter…`, `montar…` | `validarDuplicidade`, `obterBancoDaOrganizacao` |

Mapper: `toResponse`, `toEntity`, `toResponseListagem` — sufixos **inglês técnicos** aceitos no projeto para mappers (contrato já usado em `ContaPagarMapper`). Métodos novos de mapper seguem o vizinho do mesmo `*Mapper`.

### Repository (Spring Data)

Prefixos do framework em inglês são **exceção permitida**: `find`, `count`, `exists`, `delete` + propriedades Java em português (`findByIdOrganizacaoAndFlAtivo`).

Não criar métodos de repository com nomes totalmente em inglês de domínio (`findActiveCustomers`).

---

## Classes de model

- `@Entity` de negócio: substantivo em português (`ContaReceber`, `AgenciaBancaria`).
- Prefixo `Central` para entidades do schema central quando já for padrão do módulo.
- **Legado em inglês** (`AuditLog`, `TenantEntity`, `ContratoRevisionEntity` por Envers): não replicar em models novos.

---

## Exceções (inglês permitido sem SPEC)

| Categoria | Exemplos |
|-----------|----------|
| Framework Java / Spring / Jakarta | `Entity`, `Transactional`, `Optional`, `Pageable` |
| Camadas e sufixos fixos do projeto | `*Controller`, `*Service`, `*Repository`, `*Request`, `*Response`, `*Mapper`, `*Filter`, `*Projection` |
| Spring Data / JPA | `findBy…`, `getReferenceById`, `Specification` |
| Mapper (vizinho) | `toResponse`, `toEntity`, `toResponseListagem` |
| Siglas e normas externas | COMPE, ISPB, CNAE, CPF, CNPJ, CEP, LC 116, NBS, JWT, HTTP |
| Integrações / providers | Tipos espelhando API externa em `provider.*.dto` |
| SPEC ou contrato explícito | Nome literal na `docs/SPEC.md` da branch |
| Código legado já em produção | Não obriga renomear fora do escopo da tarefa; **não copiar** o inglês em feature nova |

Colunas legadas como `status`, `database_name` em `CentralOrganizacao` ou `tp_status` em várias tabelas: manter até migration dedicada; em **coluna nova** preferir `tp_situacao`, `nm_banco_dados`, etc.

---

## Tríade (validador)

Para cada campo novo:

1. Nome na SQL (português + prefixo)
2. `@Column(name = "...")` e campo Java com o mesmo significado
3. DTO/JSON com o mesmo prefixo em camelCase

Divergência entre SPEC literal e diff → `EV-DDL-001`. Inglês de domínio em código novo sem exceção → `EV-NOM-003` / `EV-NOM-004`.

---

## Checklist (código novo)

- [ ] Nenhuma coluna/campo `name`, `active`, `email` genérico — usar `nm_`, `fl_`, `ds_email` conforme o caso.
- [ ] Métodos de service/controller em português.
- [ ] Classe de entity em português.
- [ ] Repository: só prefixos Spring em inglês; propriedades em português.
- [ ] SPEC com nome literal em inglês? Documentar na SPEC como exceção consciente.

---

## Vizinhos

| Camada | Referência |
|--------|------------|
| SQL + `id_` tudojunto | `db/migration`, [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md) |
| Entity | `Banco.java` |
| Service | `BancoService` |
| DTO JSON | [`dtos.md`](dtos.md) |
| Legado inglês pontual | `EntidadeStatusRequest.ativo`, `CentralOrganizacao.status` |
