# Crítico — consumidor da API (front)

Assuma SPA ou cliente HTTP. Evidência no diff (handler, filtro, service, migration).

| Padrão | Evidência no diff | Impacto para o usuário |
|--------|-------------------|-------------------------|
| Cross-tenant ou dado de outra org na resposta | Query/service sem `idOrganizacao`; JWT sem validar vínculo | Vê dados de outra organização |
| Rota expõe PII sem auth alinhada | `permitAll` + dados sensíveis | Acesso indevido por URL |
| Sessão destruída em cascata | Refresh/logout limpa cookies em falha paralela; rotação inválida derruba access válido | Loop de login após autenticar |
| Auth bypass ou permissão ignorada | Filtro removido; `GLOBAL_*` errado em rota tenant | Módulo sem permissão |
| Migration impede subida | `EV-PER-006`, SQL que quebra Flyway | Sistema indisponível |
| Corpo de erro vaza segredo | Stack, SQL, token em `mensagem`/`debugMessage` | Risco de segurança |
| 2FA / troca de senha bypass | Filtro não aplicado no caminho alterado | Proteção de conta neutralizada |

## Sinais no diff (tendência a Crítico)

- `SecurityConfig` / filtros enfraquecidos sem compensação documentada  
- Migration com `DROP`/`NOT NULL` sem backfill em tabela populada ([`../../padrao/banco.md`](../../padrao/banco.md))  
- `V*.sql` versionada apagada ou reescrita no diff do escopo  

## Evidência

Regra ou doc (`EV-*`, `docs/padrao/…`), arquivo/trecho, entrada → resultado errado, impacto.

Defeitos que **impedem uso** mas não são segurança → em geral [`../importante/consumidor-api.md`](../importante/consumidor-api.md).
