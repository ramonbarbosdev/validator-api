# Como definir uma padronização

Toda padronização vira uma entrada em `rules/padroes.yaml`. Escolha o `tipo` pela frase que descreve o seu padrão.

| Seu padrão diz... | Tipo | Exemplo |
|---|---|---|
| "nome de X deve seguir o formato Y" | `nomenclatura` | colunas `id_`, `tp_`, `nm_`; classes PascalCase; URL kebab-case; nome de migration |
| "X deve ter / não pode ter anotação ou JavaDoc" | `declaracao_exige` | método público com JavaDoc; `@RequestBody` com `@Valid`; controller sem `@Transactional` |
| "não pode ter comentário" | `comentarios` | só JavaDoc em declarações |
| "não pode usar tal coisa no código" | `proibido` | `System.out.println`, `new Date()` |
| "camada A não pode importar camada B" | `dependencia_proibida` | controller não importa repository |
| "se existe A, tem que existir B no PR" | `par_obrigatorio` | service novo → teste novo |
| "depende de entendimento" (não dá para checar por código) | `llm` | reutilizar shared, coerência com docs |

Se um padrão não cabe nos seis primeiros, use `llm`. Quando você notar que o LLM erra uma regra com frequência, é sinal de que ela merece virar um tipo estático.

## Campos comuns
`id`, `tipo`, `severidade` (CRITICO | IMPORTANTE | MELHORIA), `arquivos` (globs, opcional), `mensagem`, `como_corrigir`, `ativa` (false desliga a regra).

## Por tipo

**nomenclatura**: `alvo` + `padrao` (regex que o nome inteiro deve casar) e/ou `proibir_padrao` (regex que o nome não pode conter).
- Alvos Java: `classe`, `interface`, `enum`, `metodo`, `construtor`, `campo`, `constante`, `parametro`, `pacote`
- Alvos SQL: `tabela_sql`, `coluna_sql`, `indice_sql`, `constraint_sql`
- Outros: `coluna_jpa` (`@Column`/`@JoinColumn`), `tabela_jpa` (`@Table`), `url_segmento` (rotas dos `*Mapping`), `arquivo` (nome do arquivo), `caminho` (caminho completo)
- `quando` (alvos Java): filtra quais declarações a regra vale.

**declaracao_exige**: `alvo` (como acima), `quando`, `exige`: lista com `{javadoc: true}`, `{anotacao: Nome}` ou `{sem_anotacao: Nome}`.

**comentarios**: `permitir_tipos` (opcional: `linha`, `bloco`). JavaDoc solto (dentro de método ou fora de declaração) também é reprovado.

**proibido**: `arquivos` + `padrao` (regex por linha). Em `.java` ignora comentários e strings; use `onde: texto` para olhar o texto bruto.

**dependencia_proibida**: `arquivos` + `importa` (regex sobre o nome completo do import).

**par_obrigatorio**: `origem` (regex do caminho, com grupos) + `destino` (usa `\1`, `\2`...); `quando: novos|alterados`; `aceitar_existente: true` aceita o arquivo já existente no repo.

**llm**: `descricao` + `arquivos`. O motor não executa; lista no JSON as regras aplicáveis ao diff para você injetar no prompt do agente.

## Filtros `quando` (declarações Java)
`anotada_com`, `sem_anotacao`, `visibilidade` (public|protected|private|package), `classe_anotada_com`, `classe_nome` (regex), `nome` (regex).

## Fluxo para adicionar uma regra
1. Escreva a entrada em `padroes.yaml`.
2. `python -m engine.motor --validar` confere o catálogo (tipos, regex, campos).
3. Adicione um teste em `tests/test_motor.py` com um caso que viola e um que não viola.
4. `pytest -q`.

## Uso
```
python -m engine.motor <base> --repo <repo da API> --saida findings-estaticos.json
```
Saída: `achados` (só em linhas adicionadas no PR), `falhas_de_regra` (uma regra quebrada não derruba as outras), `regras_executadas`, `regras_inativas`, `regras_llm_aplicaveis`. Código de saída 1 se houver achados e 2 se o catálogo for inválido.

Dependências: `pip install tree-sitter tree-sitter-java pyyaml pytest`.
