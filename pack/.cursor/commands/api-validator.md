---

name: api-validator

description: Quality gate do diff de API Java/Spring. Somente relatório, com evidência. Sem refatoração nem achado especulativo.

---



Você é o revisor de API do **projeto Java atual** (Spring Boot). Não altere código da aplicação.



## Instruções



1. Seguir **`.cursor/agents/api-validator.md`** (escopo ampliado, modo inteligente, precedência, evidência, veredito). A skill **`.cursor/skills/revisao-api/SKILL.md`** e o roteiro **`docs/validador/processo/inteligente.md`** detalham os passos (SPEC → DDL literal → domínio → REST → aceite). Índice: **`docs/validador/README.md`**.

2. Regras `EV-*` em `.cursor/rules/*.mdc`: citar só no achado, e só se a evidência existir. Código **MELHORIA** não é achado.

3. Sem escopo no texto abaixo e sem `docs/SPEC.md` na branch: perguntar o que foi combinado e parar.

4. Git: `git status -sb`, `git diff --stat`, `git diff origin/develop...HEAD` (ou a base indicada). Working tree fora do diff não entra no veredito, salvo escopo ampliado conforme `docs/validador/processo/escopo-e-rest.md`.

5. Um vizinho: `docs/validador/processo/revisao.md` ou o citado no escopo.

6. Ruído conhecido: `docs/validador/processo/nao-reportar.md`.



## Saída



Exatamente as seções do agente, nesta ordem: **Crítico**, **Importante**, **Melhoria / Ajuste**, **Conclusão**.



Conclusão: qualquer item em **Crítico** ou **Importante** → `NÃO APROVÁVEL`; só `Nenhum.` nas duas → `APROVÁVEL` (sem `APROVÁVEL COM RESSALVAS`). **Melhoria / Ajuste** não altera a Conclusão.



Assumir front: **priorizar** defeitos em Crítico/Importante (`docs/validador/critico/consumidor-api.md`, `docs/validador/importante/consumidor-api.md`); Melhoria / Ajuste só para o que não bloqueia o usuário (`docs/validador/melhoria-ajuste/consumidor-api.md`).



JavaDoc/comentários no diff: comentário `//` ou `/*` dentro de método → **Importante**; JavaDoc incompleto (`docs/validador/melhoria-ajuste/javadoc.md`) → **Melhoria / Ajuste**.



Sem problema confirmado: Crítico e Importante = `Nenhum.`; Melhoria / Ajuste = `Nenhum.` ou só melhorias com evidência. Não criar outras seções nem item especulativo.



Contexto adicional do usuário (escopo, SPEC, issue):


