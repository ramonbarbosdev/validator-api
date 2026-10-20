# SPEC — <título da tarefa>

> Autocontido: quem implementa e quem revisa usa só este documento + o diff. Se precisar explicar por fora, falta algo aqui.

**Tarefa:** #<id>  
**Branch:** `feature/<id>/<slug>`  
**Módulo:** <ex.: financeiro / cadastros / contrato>  
**Status:** rascunho | aguardando aprovação | aprovado

## Problema

O que está errado ou faltando hoje, em comportamento observável (2–4 linhas). Sem solução aqui.

## Resultado esperado

O que passa a ser verdade quando estiver pronto.

- <ex.: ao salvar conta a receber, adicionais usam `idTipoDocumentoFinanceiro` como conta a pagar>
- <...>

## Arquivos e interfaces envolvidos

| Arquivo | Ação | O que muda |
|---------|------|------------|
| `src/main/java/.../XxxController.java` | alterar | <endpoint, contrato> |
| `src/main/resources/db/migration/V...sql` | criar | <colunas/tabelas> |
| `src/test/java/.../XxxServiceTest.java` | criar | <caso> |

## Contrato HTTP (obrigatório se a feature expõe ou consome API)

Liste **cada** chamada que o front ou integrador fará. O validador usa isto no **escopo ampliado** (`docs/validador/processo/escopo-e-rest.md`).

| Método | Path | Quando | Status / corpo esperado |
|--------|------|--------|-------------------------|
| POST | `/contratos/importacoes` | upload PDF | 201 + `previa`; 422 se análise falhar |
| GET | `/contratos/importacoes/{id}` | buscar importação | 200; **não** usar `GET /contratos/importacoes` sem id |

Rotas que **não** devem ser usadas (evitar colisão com `/{id}`):

- `<ex.: GET /contratos/importacoes sem id — não existe; cai em GET /contratos/{id}>`

Exemplo de payload:

```http
PUT /conta-receber/{id}
{ "idTipoDocumentoFinanceiro": 134, ... }
```

**Padrão a seguir (vizinho no repo):** `<caminho/analogo.java>` + doc `docs/<feature>.md` se existir.

## Fora de escopo

- <ex.: não remover `ContaReceberRecebimentoController` nesta tarefa>
- <ex.: não alterar permissões em `db/central`>
- <ex.: não refatorar legado de contrato/rateio>

## Riscos e decisões

- **Migration tenant (`db/migration`):** sim/não — não editar V já aplicada.
- **Migration central (`db/central`):** sim/não — permissões conforme `docs/migrations-permissoes.md`.
- **Contrato de API quebrado:** sim/não.
- **Catálogo central (sem FK tenant):** validação no service, não FK cross-DB.
- **Raio de impacto:** quem mais usa a classe alterada?

## Critérios de aceite

- [ ] <critério verificável sim/não>
- [ ] Diff limitado aos arquivos da tabela acima (exceto merge de `develop`)
- [ ] Tenant: operações filtram `idOrganizacao` do contexto
- [ ] DDL novo espelhado em entity + DTO/`validar()` quando aplicável

## Verificação

```bash
mvn -q -Dtest=XxxServiceTest test
```

Fluxo manual (se necessário): `<GET/POST ...>` com payload de exemplo.
