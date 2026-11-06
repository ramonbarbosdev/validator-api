# Proposta de ajuste do prompt (revisão humana)

Trechos do prompt do agente (`pack/.cursor/agents/api-validator.md` e `pack/scripts/ci-api-validator.py`) que, na leitura desta mudança, **reduzem recall**: fazem o LLM deixar de publicar violações reais da padronização. Nada abaixo foi aplicado; a semântica de "o que nunca é achado" e "sem evidência, não publique" segue igual.

Contexto: com o motor estático (`pack/engine` + `pack/rules/padroes.yaml`), regras objetivas não dependem mais do LLM. Os trechos abaixo continuam válidos para o que é semântico, mas estão redigidos de forma ampla e acabam cobrindo também padronização objetiva.

## 1. "Precisão > quantidade"

- **Onde:** `api-validator.md`, linha 5: `**Precisão > quantidade.** Sem evidência suficiente, não publique o item. Hipótese não entra no relatório.`
- **Efeito:** em dúvida, o modelo omite. Para padronização (nome, anotação, comentário), a evidência é o próprio trecho do diff, mas o modelo trata como "estético".
- **Sugestão:** `**Precisão > quantidade.** Sem evidência no diff, não publique. Violação de padronização documentada (regra EV-* com trecho do diff que a contraria) é evidência suficiente — não exige demonstrar impacto em produção.`

## 2. IMPORTANTE só com "comportamento incorreto comprovado"

- **Onde:** `api-validator.md`, tabela "Mapeamento EV → severidade": `| IMPORTANTE + comportamento incorreto comprovado | Seção **Importante** |` e a lista "O que pode virar achado", item 5: `` `EV-*` **IMPORTANTE** violado com comportamento incorreto comprovado (não por ausência estética). ``
- **Efeito:** regras IMPORTANTE de forma (EV-NOM-003, EV-NOM-004, EV-DTO-001, EV-ARC-005, EV-SVC-002 em controller) quase nunca têm "comportamento incorreto"; o modelo descarta.
- **Sugestão:** `| IMPORTANTE + violação comprovada no diff (trecho que contraria a regra; impacto quando a regra for de comportamento) | Seção **Importante** |`

## 3. MELHORIA nunca é reportada

- **Onde:** `api-validator.md`, mesma tabela: `| MELHORIA (`EV-*-` MELHORIA) | Não reportar |`
- **Efeito:** contradiz a seção **Melhoria / Ajuste** do relatório. Regras como EV-NOM-001 (URL kebab-case), EV-TST-005 e EV-VAL-003 nunca aparecem. O motor já publica EV-NOM-001 em Melhoria / Ajuste, então hoje o relatório e o agente divergem.
- **Sugestão:** `| MELHORIA (`EV-*` MELHORIA) com trecho no diff | Seção **Melhoria / Ajuste** (não altera Conclusão) |`

## 4. "Estilo, rename" nunca é achado

- **Onde:** `api-validator.md`, "O que nunca é achado": `- Estilo, rename, legado fora do diff **e** fora do escopo ampliado (SPEC/REST/validação).`
- **Efeito:** a vírgula permite ler "Estilo" e "rename" como sempre proibidos, mesmo no diff. Nomenclatura em português (EV-NOM-003/004) é exatamente "rename".
- **Sugestão:** `- Estilo, rename ou legado **fora do diff** e fora do escopo ampliado. Código novo no diff que viola regra EV-* de nomenclatura ou comentário **é** achado.`

## 5. Ausência de anotação/método não é achado

- **Onde:** `api-validator.md`, tabela de mapeamento: `| Ausência (teste, annotation, interface, Optional, método extra) | Não reportar, salvo exigência explícita do escopo, da doc canônica, ... |`
- **Efeito:** `@Valid` ausente (EV-REST-002) e JavaDoc ausente (EV-SVC-002) são "ausência de annotation" e são descartados, embora estejam na doc canônica (`.mdc`).
- **Sugestão:** deixar explícito: `... salvo exigência explícita do escopo ou de regra EV-* (ex.: @Valid em @RequestBody, JavaDoc em público novo) ...`

## 6. Hipótese / "boa prática"

- **Onde:** `api-validator.md`, "O que nunca é achado": `- Hipótese (“normalmente deveria existir”, “boa prática”).`
- **Efeito:** o modelo classifica regra do projeto como "boa prática" e descarta.
- **Sugestão:** `- Hipótese ou boa prática **não documentada**. Regra listada em `.cursor/rules/*.mdc` não é hipótese.`

## 7. Prompt do CI: exigência de dois arquivos citados

- **Onde:** `ci-api-validator.py`, `build_prompt`: `**Proibido** entregar so o esqueleto ... citar **pelo menos dois** caminhos de arquivo do diff ... — em achado ou em 1-2 frases objetivas do que mudou (ex. em Melhoria).`
- **Efeito:** não reduz recall diretamente, mas leva o modelo a preencher Melhoria com resumo do diff em vez de achados, e o gate aceita isso como "análise".
- **Sugestão:** `Cite os arquivos do diff que voce analisou em uma linha "Arquivos analisados: ..." no fim de Melhoria / Ajuste; nao use resumo do diff como achado.`

## 8. EV-TST: ausência de teste nunca é achado

- **Onde:** `api-validator.md` (`EV-TST-*: falta de @WebMvcTest ou de teste novo **não** é achado.`) e `testing.mdc`.
- **Efeito:** EV-TST-001..004 estão no catálogo como IMPORTANTE e nunca disparam.
- **Sugestão:** decidir explicitamente: rebaixar EV-TST-001..004 para MELHORIA no `.mdc` **ou** criar regra `par_obrigatorio` no motor (ex.: controller novo exige `*ControllerTest`). Hoje a regra existe no papel e é desligada no prompt.
