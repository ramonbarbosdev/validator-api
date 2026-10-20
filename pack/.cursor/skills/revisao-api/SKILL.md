---

name: revisao-api

description: Revisa o diff de API Java/Spring no escopo pedido (SPEC, DDL literal, domínio, REST). Usa .cursor/agents/api-validator.md e docs/validador/. Acionar com /api-validator, api-validator ou revisão de PR/feature.

---



# Revisão de diff (API Java / Spring)



Quality gate do diff. Com **escopo ampliado**, inclui SPEC, REST e testes conforme o agente.



**Fonte de verdade do procedimento:** `.cursor/agents/api-validator.md`. **Padrões:** `docs/padrao/README.md`. **Índice validador:** `docs/validador/README.md`. **Overlay de vizinhos (opcional):** `docs/validador/revisao.overlay.md`.



## Passos



1. Escopo: texto após `/api-validator`, `docs/SPEC.md` na branch, issue citada ou **Discussao na PR** (CI / `.api-validator-review/pr-*-discussion.md`). Sem escopo, perguntar e parar.

2. Ler `docs/validador/processo/inteligente.md` e seguir o roteiro SPEC (resultado → DDL → domínio → HTTP → aceite).

3. Ler `docs/validador/processo/escopo-e-rest.md` e decidir se o **escopo ampliado** está ativo.

4. `git status -sb` e `git diff origin/develop...HEAD --stat` (ou base indicada no escopo).

5. Ler `docs/validador/processo/nao-reportar.md` antes de achados marginais.

5b. Auth/erros/validação no diff: **primeiro** `docs/validador/critico/consumidor-api.md` + `docs/validador/importante/consumidor-api.md`; **depois** `docs/validador/melhoria-ajuste/consumidor-api.md` (Melhoria / Ajuste, só polish).

6. Checklist: `docs/validador/processo/review-checklist-api.md` (seções pertinentes).

7. Regras `EV-*` em `.cursor/rules/*.mdc` só nas áreas tocadas pelo diff/SPEC.

8. Vizinho: `docs/validador/processo/revisao.md` + `revisao.overlay.md` se existir.

9. Fluxo: controller → DTO/`validar()` → service → repository → SQL.

10. Migration: dados/integridade e subida segura (`EV-PER-006`, `docs/padrao/banco.md`); depois DDL literal + `@Column` + DTO vs SPEC (`EV-DDL-001`).

11. Domínio na SPEC: service implementa estratégia descrita.

12. REST: paths da SPEC vs controllers (`EV-REST-006`).

13. Testes tocados: `mvn -q -Dtest=... test`.

13b. Service/controller/security no diff: `importante/codigo-javadoc-comentarios.md` — inline no método → Importante; JavaDoc fraco → `melhoria-ajuste/javadoc.md` (Melhoria / Ajuste).

14. Saída do agente: **Crítico**, **Importante**, **Melhoria / Ajuste**, **Conclusão** (Conclusão só no artefato CI; comentário na PR omite Conclusão).



## Delegação



Comando: `.cursor/commands/api-validator.md`. Não alterar código da aplicação na revisão.


