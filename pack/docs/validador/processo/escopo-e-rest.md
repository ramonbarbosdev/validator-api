# Validador — escopo ampliado e contrato HTTP

Complementa `.cursor/agents/api-validator.md`. Quando o **escopo ampliado** estiver ativo, o veredito não se limita ao `git diff`: inclui o que a SPEC e o contrato HTTP exigem para a atividade fechar.

## Quando ativar o escopo ampliado

Ative se **qualquer** condição for verdadeira:

1. Existe `docs/SPEC.md` na branch (ou SPEC colada no comando `/api-validator`).
2. O diff altera `*Controller.java`, records de resposta/request expostos na API (`*Response`, `*Request` usados em controller), ou `ContratoImportacao*`.
3. O comando cita integração, rotas HTTP, front, polling ou PR com contrato de API.
4. O diff adiciona ou altera validação de domínio (enum whitelist, `validar()` mais restritivo).

Se nenhuma condição for verdadeira, vale só o diff (modo gate enxuto).

## O que conferir no escopo ampliado

### 1. SPEC vs diff

- Cada item marcado em **Resultado esperado** e **Critérios de aceite** deve estar implementado no diff ou já no `develop` (indicar qual).
- Arquivos fora da tabela da SPEC entram como achado só se forem desnecessários ou perigosos (tenant, segurança).

### 2. Rotas HTTP da SPEC

Para cada linha do bloco **Contrato HTTP** da SPEC:

| Verificação | Falha típica |
|-------------|----------------|
| Existe handler com mesmo método e path (prefixo `/api` implícito no deploy) | Front chama URL que não existe |
| Status e envelope (`ApiResponseDTO`) coerentes com vizinho do módulo | 201 vs 200, 422 de negócio |
| Path com segmento fixo não é engolido por `{id}` de outro controller no mesmo prefixo | `GET /contratos/importacoes` → `GET /contratos/{id}` com `id=importacoes` |

### 3. Colisão `{pathVariable}` vs segmento fixo

Procedimento (evidência obrigatória no achado):

1. Listar paths **fixos** usados pela feature (SPEC ou controller do diff), ex.: `/contratos/importacoes`.
2. Buscar no pacote `controller` outros `@RequestMapping` cujo prefixo seja ancestral do path fixo, ex.: `@RequestMapping("/contratos")` + `@GetMapping("/{id}")`.
3. Se existir template `/{id}` (ou `{idContrato}`, etc.) no ancestral e **não** existir handler no controller correto para o path fixo com o **mesmo método** que o cliente usa, é colisão.

Exemplo real: `ContratoImportacaoController` — `POST` e `GET /{id}` sob `/contratos/importacoes`; não há `GET` em `/contratos/importacoes`. `ContratoController` expõe `GET /contratos/{id}` → `GET /contratos/importacoes` quebra com `MethodArgumentTypeMismatchException`.

Correções aceitas: handler explícito, mudar prefixo, `@Order` + mapeamento mais específico documentado, ou SPEC/front restritos ao path que existe.

### 4. Validação mais restritiva (whitelist)

Se o diff passa a validar código contra enum/lista fechada (`ItemLc116`, `CodigoNbs`, etc.):

- Comparar formato persistido (testes com `setCdLc116("1.01")`, dados legados) com o que `validar()` aceita.
- Se aceite da SPEC exige migração/normalização de dados, ausência no diff é achado **Importante** quando o critério de aceite citar legado ou edição de registros antigos.

### 5. Testes e compilação

Se o diff mexe em `src/test/**` ou altera assinatura de record usado em teste:

- Executar `mvn -q -Dtest=<classes tocadas> test` (ou suíte do módulo indicada na SPEC).
- Falha de compilação ou teste existente = achado **Importante** (ou **Crítico** se impedir merge).

## O que continua fora do veredito

- Refatorar legado não citado na SPEC.
- Performance sem cenário demonstrado no escopo.
- Front-end (salvo contrato HTTP na SPEC).
- Atualizar `docs/arquitetura-banco-atual.md`.

## Comando sugerido

```text
/api-validator #430 — docs/SPEC.md na branch, escopo ampliado (REST + aceite)
```
