# Padrões (pacote cursor-api-validator-java)

Convenções **genéricas** para APIs Java/Spring. O projeto alvo pode estender `docs/padrao/` após o install.

Precedência: **SPEC da branch** → regras `EV-*` CRÍTICAS → docs desta pasta → código vizinho.

| Documento | Uso |
|-----------|-----|
| [`nomenclatura-portugues.md`](nomenclatura-portugues.md) | PT em método, model, coluna/campo |
| [`banco.md`](banco.md) | Flyway, dados/integridade (`EV-PER-006`), schemas, tenant, tríade |
| [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md) | `id_` / `nm_<tudojunto>`, tríade DDL |
| [`dtos.md`](dtos.md) | Request/Response/Filter |
| [`controllers.md`](controllers.md) | Controller fino → service |
| [`services.md`](services.md) | Negócio, JavaDoc, repository |
| [`listagem-paginada-filtrada.md`](listagem-paginada-filtrada.md) | `listar` + Filter + Pageable |

**Validador:** [`../validador/README.md`](../validador/README.md)

**Overlay e-Simples (Padrão C, mestre–detalhe):** instalar stack `java-spring-esimples` — ver `stacks/java-spring-esimples/README.md` no repositório do pacote.

Regras Cursor: `.cursor/rules/*.mdc`
