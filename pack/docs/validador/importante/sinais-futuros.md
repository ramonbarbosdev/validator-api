# Importante — sinais de “futuro erro” no diff

Se o change **introduz** ou **amplifica** (com evidência de quebra no fluxo entrada → resposta), classifique **Importante** ou **Crítico** — não espere o front quebrar na PR.

| Sinal no diff | Classificação típica |
|---------------|----------------------|
| `catch` vazio ou `return false` sem resposta clara em auth | Importante / Crítico |
| GET coleção sem tenant/listagem do vizinho | Importante (`EV-LST-*`, `EV-MTN-*`) |
| `SecurityConfig`/filtros alterados sem alinhar rotas públicas | Importante / Crítico |
| Handler mapeia exceção de negócio para 500 em vez de 422 | Importante |
| Cookie path/domain incoerente (homolog no escopo) | Importante |

Detalhes consumidor: [`consumidor-api.md`](consumidor-api.md). Segurança/tenant: [`../critico/`](../critico/).
