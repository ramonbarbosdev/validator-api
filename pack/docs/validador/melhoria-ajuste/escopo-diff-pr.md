# Melhoria / Ajuste — PR maior que a task (diff ampliado)

**Não confundir** com [`escopo-e-rest.md`](../processo/escopo-e-rest.md) (**escopo ampliado** do validador): lá o revisor **lê mais** que o patch (SPEC, rotas HTTP). Aqui o assunto é a **entrega**: a PR **mudou mais código** do que o combinado da atividade/issue/SPEC/título da branch.

## Quando reportar

Reporte em **Melhoria / Ajuste** (não bloqueia `APROVÁVEL`) quando **todas** forem verdadeiras:

1. Há **escopo explícito** (issue, card, `docs/SPEC.md`, título da PR/branch ou discussão humana na PR) apontando **uma feature ou correção** concreta.
2. O `git diff` traz **mudanças grandes ou claramente de outro assunto** além desse núcleo — por exemplo:
   - refatoração extensa em service/mapper **sem** ligação direta com o aceite;
   - extração/reorganização de centenas de linhas “de passagem”;
   - conserto em outro módulo (ex. plano nulo, central) **não citado** no escopo da task.
3. Isso **não** é defeito funcional comprovado (senão vai em **Importante**/**Crítico**).
4. Discussão na PR **não** justifica explicitamente “tudo na mesma PR” (se justificar, **não** reporte ou cite a justificativa e só reporte o que ainda for excesso).

Use `git diff --stat` e leitura dos arquivos com mais linhas alteradas. Cite **2+ arquivos** do diff com **o que** mudou em uma frase cada (não só o nome do arquivo).

## O que **não** é este achado

- Código legado fora do diff → [`nao-reportar.md`](../processo/nao-reportar.md).
- Aceite da SPEC não entregue → **Importante** / **Crítico** ([`inteligente.md`](../processo/inteligente.md)).
- “Poderia extrair método” sem volume relevante → não reportar.

## Formato obrigatório no relatório

Título sugerido: **PR trouxe mais mudanças do que a task** ou **Entrega misturou feature X com refatoração Y**.

Use estes campos (linguagem que qualquer dev do time entende — **evite** só a palavra “diff ampliado” sem explicar):

| Campo | Conteúdo |
|-------|----------|
| **Onde** | Arquivos do patch + resumo objetivo (ex.: “~200 linhas extraídas no mapper”, “service refatorado além do ramo SUPRESSAO”). |
| **O que a task pedia** | Uma frase: issue/SPEC/título/PR (cite número ou nome se constar no prompt). |
| **O que veio a mais** | Lista curta do que não parece parte desse pedido (com evidência no diff). |
| **Para o usuário final** | Em geral: **não há bug visível na tela** — escreva `N/A (revisão e manutenção)` ou descreva impacto se houver. |
| **Em linguagem simples** | **2–4 frases**, analogia permitida: “pediu-se trocar a fechadura; a PR também reorganizou armários e outro cômodo”. Deixe claro que **não é acusação de código errado**, e sim **entrega pesada e misturada**. |
| **Por que importa** | Revisão difícil, rollback arriscado, histórico confuso — uma linha cada ou um parágrafo curto. |
| **Melhoria** | Ação concreta: **próximas PRs** separar feature da refatoração; ou mover trecho X para outra task (esta PR pode seguir se o time aceitar o risco). |

Se o ponto já foi debatido na PR, referencie **discussão na PR** (autor ou trecho) no campo **O que veio a mais** ou **Melhoria**.

## Exemplo (estrutura)

```text
* **PR trouxe mais mudanças do que a task de supressão**

  * **Onde:** `ContratoMapper.java` (extração ~217 linhas); `ContratoService.java` (refatoração além dos ramos SUPRESSAO); `CentralPlatformService.java` (id_plano nulo no row mapper)
  * **O que a task pedia:** aditivo/supressão de contrato (PR #527 / feature 521)
  * **O que veio a mais:** refatoração ampla de mapper e service; ajuste de plano nulo em serviço central não citado no escopo da supressão
  * **Para o usuário final:** N/A (revisão e manutenção)
  * **Em linguagem simples:** A entrega da supressão veio no mesmo pacote que outras mudanças grandes. A feature pode estar certa; o problema é misturar vários assuntos numa única aprovação.
  * **Por que importa:** Quem revisa precisa validar tudo junto; se algo falhar em produção, fica difícil desfazer só a parte da supressão.
  * **Melhoria:** Nas próximas entregas, limitar a PR ao que a task pede; refatorações e consertos paralelos em PR separada.
```

## Referência interna

Código de regra (só na análise, **não** imprimir `EV-*` no relatório público): **EV-ENT-001** — entrega / escopo da PR vs combinado da atividade.
