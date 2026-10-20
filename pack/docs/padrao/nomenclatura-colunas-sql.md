# Padrão de nomenclatura — colunas SQL (tenant)

Parte da norma de **português em todo o sistema**: [`nomenclatura-portugues.md`](nomenclatura-portugues.md) (`EV-NOM-003`).

Referência para **SPEC**, implementação e **validador** (`EV-DDL-001`). Quando a SPEC de uma tarefa fixar nomes literais, a SPEC **prevalece** sobre este documento para aquela tarefa.

## Tabelas

- Nome da tabela: substantivos em `snake_case` com `_` entre palavras (`entidade_dependente`, `conta_receber`).
- Um arquivo Flyway por versão; não editar `V*.sql` já aplicada em ambiente compartilhado.

## Colunas

| Prefixo | Uso | Corpo do identificador |
|---------|-----|-------------------------|
| `id_` | Chaves, FKs, identificadores | **Uma palavra composta**, sem `_` extra após o prefixo |
| `nm_` | Nomes, rótulos textuais curtos | Mesmo: `nm_<tudojunto>` |
| `fl_` | Flags booleanas | `fl_ativo`, `fl_principal` |
| `dt_` | Data/hora | `dt_criacao`, `dt_desativacao` |
| `cd_` | Códigos | `cd_compe` (quando já existir no módulo) |

### Regra `id_<tudojunto>` / `nm_<tudojunto>`

Após `id_` ou `nm_`, **não** inserir underscores entre os tokens semânticos:

| Válido (padrão novo em SPEC) | Inválido se a SPEC pedir tudojunto |
|------------------------------|-------------------------------------|
| `id_entidadesuperior` | `id_entidade_superior` |
| `id_entidadedependente` | `id_entidade_dependente` |
| `nm_razaosocial` | `nm_razao_social` |

Legado no repositório (`id_entidade_subcategoria`, etc.) permanece até migração explícita; **vizinho legado não anula SPEC da tarefa**.

### PK vs FK

Cada coluna tem **um** papel. PK do vínculo e FK da entidade dependente **não podem** ter o mesmo nome SQL.

Na SPEC, incluir glossário com três identificadores distintos (exemplo a adaptar na tarefa):

| Papel | Exemplo (`tudojunto` distinto para cada coluna) |
|-------|--------------------------------------------------|
| PK da linha em `entidade_dependente` | `id_vinculoentidadedependente` |
| FK → `entidade` (cliente da aba) | `id_entidadedependente` |
| FK → `entidade` (superior) | `id_entidadesuperior` |

O validador **não inventa** nomes: só compara diff com o glossário da SPEC.

## Constraints e índices

- `pk_<tabela>` / `fk_<tabela>_<papel>` / `uk_<tabela>` / `ck_<tabela>_<regra>` / `idx_<tabela>_<colunas>`
- Mensagens amigáveis: `ConstraintMessageMap` com a **chave exata** retornada pelo Postgres.

## Tríade (validador)

Para cada coluna nova na SPEC:

1. `db/migration/V*.sql`
2. `@Column(name = "...")` na entity
3. Regra de negócio no service (e CHECK na SQL quando a SPEC exigir)

Divergência de nome entre (1) e (2), ou entre diff e SPEC literal → achado **Importante** (`EV-DDL-001`).
