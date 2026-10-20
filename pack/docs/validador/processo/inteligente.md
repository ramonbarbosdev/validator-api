# Validador inteligente (api-validator)

Como fazer o `/api-validator` ir além do “diff bonito”: cruzar **intenção da SPEC**, **modelo de dados**, **domínio** e **contrato HTTP** com evidência no código.

Procedimento completo de veredito: `.cursor/agents/api-validator.md`. Passos operacionais: `.cursor/skills/revisao-api/SKILL.md`. Índice de todos os padrões: `docs/padrao/README.md`.

## O que “inteligente” significa aqui

| Não é | É |
|-------|---|
| Achar mais itens por instinto | Comparar diff com **fontes de verdade** na ordem de precedência |
| Sugerir refatoração | Dizer o que a SPEC pediu e **não está** no diff (ou está diferente) |
| Copiar estilo do vizinho legado | Respeitar SPEC com nomenclatura literal (`EV-DDL-001`) |
| Revisar o repo inteiro | Escopo ampliado: SPEC + REST + tríade DDL + critérios de aceite |

## Entrada mínima

1. Texto após `/api-validator` **ou** `docs/SPEC.md` na branch.
2. `git diff origin/develop...HEAD` (ou base indicada).
3. Decisão de escopo ampliado: [`escopo-e-rest.md`](escopo-e-rest.md).

Sem (1): perguntar escopo e parar.

## Roteiro de leitura (antes do diff)

Ler na SPEC (ou no texto do comando), nesta ordem:

1. **Resultado esperado** — lista de verdades que devem passar a valer.
2. **Modelo de dados / DDL** — tabela, colunas **literais**, CHECK/UK, glossário PK/FK.
3. **Estratégia de domínio** — parágrafos “Importante” (ex.: vínculo registrado da dependente para a superior; histórico por desativação).
4. **Contrato HTTP** — método, path, status, payload.
5. **Critérios de aceite** — checkboxes verificáveis.
6. **Fora de escopo** — não reportar como falta.

## Matriz SPEC → evidência no diff

| Bloco na SPEC | Onde olhar no diff | Falha típica → seção |
|---------------|-------------------|----------------------|
| Nome de tabela/coluna literal | `V*.sql`, `@Column`, `ConstraintMessageMap` | **Importante** (`EV-DDL-001`) |
| CHECK/UK citados na SPEC | migration + service (mensagem 422) | **Importante** se SPEC exige CHECK e SQL não tem |
| Estratégia de domínio | service (quem é “lado A” do FK), não modelar inverso | **Importante** se modelo inverte o combinado |
| Linha do Contrato HTTP | `*Controller.java` | **Importante** / **Crítico** (tenant) |
| Aceite “front” | outro repo ou paths citados na SPEC | **Importante** se escopo inclui front e não há integração |
| Tenant / mesma org | `TenantContextService`, queries com `idOrganizacao` | **Crítico** (`EV-MTN-*`) |
| Colisão `/{id}` | grep controllers ancestral | **Importante** (`EV-REST-006`) |

## Nomenclatura `id_<tudojunto>`

Quando a SPEC disser **“manter exatamente os nomes”**:

1. Extrair lista de identificadores da SPEC (grep mental: backticks ou tabela de colunas).
2. Para cada um: `grep` no diff em `migration`, `model`, `ConstraintMessageMap`.
3. Vizinho com `id_entidade_subcategoria` **não** justifica renomear se a SPEC da #647 disser `id_entidadesuperior`.

Doc canônico: `docs/padrao/nomenclatura-colunas-sql.md`.

## Domínio em linguagem natural

Se a SPEC descreve **como** o negócio funciona (não só DDL):

- Traduzir para invariantes verificáveis (ex.: “não cadastrar superior como entidade que possui dependentes” → uma linha por par dependente/superior; superior não é dono do relacionamento).
- Procurar no **service** do diff: validações equivalentes (auto-vínculo, duplicata, ciclo, org).
- Se o texto da SPEC exige histórico por **desativação** e o diff só faz `DELETE` sem `fl_ativo`/`dt_desativacao` → **Importante** (se aceite citar desativação).

## Saída

Sempre o formato do agente: **Crítico**, **Importante**, **Conclusão**.

## Comando sugerido

```text
/api-validator docs/SPEC.md — escopo ampliado, validador inteligente (DDL literal + domínio + REST)
```

## Manutenção

- Novo padrão global de coluna → atualizar `docs/padrao/nomenclatura-colunas-sql.md` + regra `EV-DDL-001`.
- Novo tipo de atividade no índice → [`revisao.md`](revisao.md).
