# Crítico — regras EV e padrões

Consultar `.cursor/rules/*.mdc` no projeto instalado. Resumo de fontes:

| Área | Regra / doc | Tema típico Crítico |
|------|-------------|---------------------|
| Segurança | `security.mdc`, `EV-SEC-*` | Bypass, exposição, permissão |
| Multi-tenant | `multi-tenant.mdc`, `EV-MTN-001/002/003` | Cross-tenant, contexto ausente |
| Persistência | `persistence.mdc`, [`banco.md`](../../padrao/banco.md), `EV-PER-006` | Migration quebra startup/dados |
| Persistência | `EV-PER-004` (elevação) | Apagar/reescrever `V*.sql` no diff |
| Arquitetura | `architecture.mdc` | Tenant em persistência central sem exceção |

**Importante** (não bloqueante só se for MELHORIA no `.mdc`): ver [`../importante/regras-ev-e-padrao.md`](../importante/regras-ev-e-padrao.md).
