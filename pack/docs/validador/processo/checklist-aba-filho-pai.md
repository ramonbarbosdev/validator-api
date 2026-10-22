# Checklist — nova aba / filho no cadastro (mestre–detalhe)

Use quando a atividade ou o diff indicam **aba**, **vínculo**, **filho** ou **sub-rota** sob um pai (`/entidades/{id}/…`, conta a pagar/receber, colaborador, contrato).

Docs de padrão: [`mestre-detalhe-conta-receber.md`](../../padrao/mestre-detalhe-conta-receber.md), [`colecao-filha-vinculada-pai.md`](../../padrao/colecao-filha-vinculada-pai.md) (stack e-Simples). Vizinho **Entidade**: `EntidadeService.criar` / `atualizar` + `EntidadeRequest`.

**Desvio do padrão** (controller só do filho, escrita só em sub-rota, etc.): aceitável se estiver **justificado** na atividade, em `docs/SPEC.md` ou em **comentários humanos na PR** (mesma precedência de escopo). O validador cita a justificativa e confere se o diff implementa o combinado — não reprova por vizinho genérico sem confrontar o texto.

## 1. Ler a intenção de persistência (SPEC ou card)

| Se a atividade diz… | O diff deve… |
|---------------------|--------------|
| Salvar **junto** com o cadastro (um botão Salvar) | Filho no `*Request` do pai **ou** documentar na SPEC que só persiste após primeiro `POST` (dois passos) |
| Aba só **consulta** após cadastro | Sub-rota `GET …/{id}/filhos` aceitável; mestre sem array pesado |
| Mesmo comportamento de outra aba do **mesmo** pai | Espelhar o filho vizinho (ex.: endereços em `EntidadeRequest` + `substituirEnderecos`) |

Sem SPEC: inferir pelo card da PR / discussão humana; se ambíguo, achado **Importante** pedindo alinhamento explícito.

## 2. Escrita (agregado)

- [ ] `EntidadeService` (ou service do pai): `criar` / `atualizar` chamam `substituir*` / `sincronizar*` para **todos** os filhos que a UI trata como aba do mesmo formulário?
- [ ] `*Request` do pai inclui lista/campo do filho **se** o vizinho equivalente inclui?
- [ ] `POST` do pai **sem** `id`: FK do filho exige pai persistido? Se sim, SPEC/front devem prever **segundo** save ou sub-rota pós-criação — senão **Crítico** (consumidor não conclui fluxo).
- [ ] Sub-rota dedicada (`*DependenteService`, etc.) **fora** da transação do `PUT` do pai: reportar **Importante** se o card promete “salvar junto”.

## 3. Leitura (mestre × aba)

- [ ] Listagem paginada: **Padrão C** — sem arrays de filhos (`toResponseListagem`).
- [ ] `GET /{pai}/{id}`: sem hidratar coleção da aba (array vazio ou omitido); totais só se o padrão do módulo exige (`toResponseComTotaisAgregados`).
- [ ] Aba: `GET /{pai}/{id}/<filho>` (ou paginado) — alinhado a conta a receber / pagamentos.
- [ ] **Controller do pai** expõe a sub-rota (`EntidadeController`, `ContaReceberController`); **não** criar controller dedicado só para o filho/aba (`EV-MD-004`), **salvo** justificativa na atividade, SPEC ou comentários humanos na PR — então validar se o diff entrega o combinado, não o padrão genérico.
- [ ] `*Response` do mestre **sem** lista do filho **não** é defeito se o front carrega a aba pela sub-rota; é **Importante** se o front só recarrega o pai após salvar.

## 4. Domínio e integridade

- [ ] Regras citadas na SPEC (ex.: só `flCliente`, sem ciclo superior/dependente) implementadas no **service** do diff.
- [ ] `deletar` do pai: FK em tabela de vínculo — limpar ou documentar restrição na SPEC.

## 5. Evidência no relatório

Cada achado: regra (`EV-MD-*` ou doc), arquivo, método, impacto no **fluxo do usuário** (salvar, aba vazia, 422 inesperado).

**Checklist `[x]` nao substitui o codigo:** pendencia que **continua** deve aparecer como **`Não corrigido`** em Importante/Crítico ou `- [ ] **Não corrigido:**` na Conferência — nunca `[x]` falso. O CI reprova `Nenhum.` quando o codigo ainda viola EV-MD-* (`verify_filho_pai_code.py`).

## 6. Analise automatica (generica)

`filho_pai_analyze.py` varre `src/main/java/**/controller`:

- **Pai + filho:** `EntidadeController` + `EntidadeDependenteController` (sufixos configuráveis: Dependente, Pagamento, Item, …).
- **Sub-rotas** no pai (`@GetMapping("/{id}/…")`) vs controller REST só do filho → **EV-MD-004**.
- **Agregado:** hint de campo no `*Request` do pai e `sincronizar*`/`substituir*` no `*Service` (heuristica; conferir no diff).

Fatos entram no **prompt do agente**; `verify_filho_pai_code.py` barra relatorio `Nenhum.` inconsistente.

| Env | Efeito |
|-----|--------|
| `CURSOR_VALIDATOR_VERIFY_FILHO_PAI_CODE=1` | Gate ativo (padrao) |
| `CURSOR_VALIDATOR_CHILD_CONTROLLER_ALLOWLIST=FooController.java` | Legado permitido (virgula) |

Comando sugerido:

```text
/api-validator docs/SPEC.md — escopo ampliado, checklist aba/filho (Entidade / clientes superiores)
```
