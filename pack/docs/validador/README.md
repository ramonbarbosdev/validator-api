# Validador de API (`/api-validator`)

Cruzar **SPEC**, **diff** e **padrões** do projeto Java/Spring.

**Agente:** [`.cursor/agents/api-validator.md`](../../.cursor/agents/api-validator.md) · **Skill:** [`.cursor/skills/revisao-api/SKILL.md`](../../.cursor/skills/revisao-api/SKILL.md)

**Padrões:** [`../padrao/README.md`](../padrao/README.md) · **SPEC:** [`../SPEC.template.md`](../SPEC.template.md)

---

## Por severidade do relatório

| Seção no relatório | Pasta | Bloqueia `APROVÁVEL`? |
|--------------------|-------|------------------------|
| **Crítico** | [`critico/`](critico/README.md) | Sim |
| **Importante** | [`importante/`](importante/README.md) | Sim |
| **Melhoria / Ajuste** | [`melhoria-ajuste/`](melhoria-ajuste/README.md) | Não |
| **Conclusão** | (só artefato CI) | — |

### Crítico

- [`critico/consumidor-api.md`](critico/consumidor-api.md) — front: tenant, bypass, vazamento, migration
- [`critico/regras-ev-e-padrao.md`](critico/regras-ev-e-padrao.md) — `EV-*` e padrões CRÍTICOS

### Importante

- [`importante/consumidor-api.md`](importante/consumidor-api.md) — contrato HTTP, auth, REST, SPEC
- [`importante/codigo-javadoc-comentarios.md`](importante/codigo-javadoc-comentarios.md) — `//` no método, JavaDoc ausente
- [`importante/sinais-futuros.md`](importante/sinais-futuros.md) — sinais no diff
- [`importante/regras-ev-e-padrao.md`](importante/regras-ev-e-padrao.md) — `EV-*` IMPORTANTE

### Melhoria / Ajuste

- [`melhoria-ajuste/consumidor-api.md`](melhoria-ajuste/consumidor-api.md) — polish de resposta HTTP
- [`melhoria-ajuste/javadoc.md`](melhoria-ajuste/javadoc.md) — padronização de JavaDoc

---

## Processo (como revisar)

[`processo/README.md`](processo/README.md) — inteligente, escopo REST, checklist, PR/CI, ruído.

**Overlay (opcional):** [`revisao.overlay.md`](revisao.overlay.md) — stack `java-spring-esimples`

```text
/api-validator docs/SPEC.md
```
