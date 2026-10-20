# Padrão C — listagem enxuta e coleção filha vinculada ao pai

Guia REST/JPA do esimples-api para:

1. **Padrão C** — o que pode (e não pode) ir no JSON da **listagem paginada**.
2. **Filho vinculado ao pai** — persistência e escrita agregada (sem CRUD HTTP independente do filho).

**Stack:** Spring Boot + JPA, `Page<…>` na listagem + `GET /{id}` no mestre.

**Detalhe do mestre e abas (sub-rotas):** [`mestre-detalhe-conta-receber.md`](mestre-detalhe-conta-receber.md) (referência Conta a receber; espelho Conta a pagar).

---

## Padrão C — listagem paginada

Única classificação de carga para **grid/listagem**. Não há faixa A/B de formulário neste documento; o `GET /{id}` e abas seguem o guia mestre–detalhe.

### Onde olhar no código

| O quê | Onde |
|-------|------|
| Listagem | `XxxService.listar(…)` → `.map(…)` até o DTO da página |

### Valores (auditoria)

| Valor | Significado |
|-------|-------------|
| **ok** | Item **enxuto**: `toResponseListagem`, DTO `*Resumo*`, ou coleções pesadas **vazias** / omitidas. Sem payload de formulário, sem metadados de UI legado. |
| **violation** | Listagem usa o **mesmo montagem do detalhe** (`toResponse` completo), embute **arrays filhos** (pagamentos, itens, endereços, …), ou troca campo de filtro por só rótulo na linha. |
| **review** | Caso limítrofe (ex.: objeto 1:1 “médio” na lista). |
| **unknown** | Não classificado (mapper indireto, export unpaged sem revisar). |
| **n/a** | Sem listagem paginada. |

`violation` em **C** é problema da **listagem** — corrigir primeiro (`toResponseListagem` ou equivalente).

### Implementação desejada

| Situação | Código |
|----------|--------|
| Listagem | `repository.findAll(spec, pageable).map(e -> mapper.toResponseListagem(e, …))` ou DTO `*Resumo*` |
| Evitar | `listar().map(mapper::toResponse)` com filhos preenchidos → **violation** |
| Export CSV/Excel | Mesmo payload da **listagem**, não do detalhe |
| Detalhe / abas | Ver [`mestre-detalhe-conta-receber.md`](mestre-detalhe-conta-receber.md) |

### N+1

**violation** em C costuma vir com **N+1**: coleção `LAZY` no `.map()` da página sem batch/graph na listagem. Listagem enxuta; graph ou agregação só onde o detalhe exige.

**Referência:** `ContaReceberRepository.findAll` sem `recebimentos`; totais no `GET /{id}`; aba em `GET /conta-receber/{id}/recebimentos`. Espelho: conta a pagar + `GET /conta-pagar/{id}/pagamentos`.

### Colisão filtro × resposta

Na listagem, manter **par id + label** quando a UI precisa de texto. **Não** reutilizar o nome do campo de filtro para enviar só rótulo. Filtros: `*Filter` + `GenericSpecificationBuilder`.

---

## Agregado pai–filho (persistência e escrita)

Filhos que só existem no contexto do pai. **Não** embutir essas coleções na listagem (**Padrão C**).

### Quando aplicar

1. FK obrigatória ao pai.
2. Ciclo de vida acoplado: CRUD do filho via salvar o pai (ou ação no controller do pai).
3. Tenant: filho com `id_organizacao` (`TenantEntity`).
4. Pai com `@OneToMany(mappedBy = …)` (`cascade` / `orphanRemoval` quando o filho não sobrevive sem o pai).

**Variante 1:1:** embutido no request/response do pai (ex.: `retencao`), sem controller do filho.

**Exceção:** sub-recurso com fluxo próprio ou permissões distintas — rotas aninhadas ou controller dedicado. Novas features que caibam nos quatro critérios **não** criam `XxxFilhoController` só por conveniência.

### Persistência

| Item | Regra |
|------|--------|
| Filho | `extends TenantEntity` |
| Relação | `@ManyToOne` pai; `@OneToMany` no pai com `mappedBy` |
| Migrations | Nova migration; não alterar `V*.sql` já aplicada |

### API REST

| Aspecto | Regra |
|---------|--------|
| `GET /{pai}` paginado | **Padrão C** — sem coleções pesadas |
| `GET /{pai}/{id}` / abas | Conforme [`mestre-detalhe-conta-receber.md`](mestre-detalhe-conta-receber.md) |
| `POST` / `PUT` pai | Body com `List<…Request>` ou 1:1; `substituir*` / `sincronizar*` no **service do pai** |
| Controller do filho | **Não** para coleção agregada clássica |
| Permissões | Alinhar ao recurso pai |

Nomenclatura típica: `substituirEnderecos`, `sincronizarPagamentos`, `sincronizarRecebimentos`, `substituirItens`.

### Módulos de referência (agregado)

| Pai | Filho(s) | Service |
|-----|----------|---------|
| `Entidade` | endereços, contatos, cnaes, dados bancários | `EntidadeService` |
| `Colaborador` | endereços, contatos, módulos | `ColaboradorService` |
| `ContaPagar` / `ContaReceber` | pagamentos/recebimentos, retencao | `ContaPagarService` / `ContaReceberService` |
| `Contrato` | itens, aditivos | `ContratoService` |

Listagem destes módulos deve tender a **C ok**; detalhe pesado em `GET /{id}` e sub-rotas (ex.: contrato — listagem sem itens/aditivos; abas em `/itens`, `/aditivos`).

---

## Manifesto (somente Padrão C)

Estado por módulo: [`carga-faixa-manifest.json`](carga-faixa-manifest.json) — campo `listagem_c` e notas em `detalhe` (texto livre).

```json
{
  "modules": {
    "financeiro/ContaReceberService": { "listagem_c": "ok" },
    "cadastros/EntidadeService": { "listagem_c": "violation", "detalhe": "filhos na listagem — alinhar toResponseListagem" }
  }
}
```

---

## Validação

| Canal | Uso |
|-------|-----|
| Este documento | **Padrão C** na listagem + regras de filho agregado |
| [`mestre-detalhe-conta-receber.md`](mestre-detalhe-conta-receber.md) | Mestre, totais, aba, escrita |
| `/api-validator` | SPEC + diff; vizinho `ContaReceber` / `ContaPagar` |
| [`../validador/README.md`](../validador/README.md) | Índice do validador e checklist |

Atividade piloto listagem: [`../SPEC-conta-pagar-listagem-faixa-c.md`](../SPEC-conta-pagar-listagem-faixa-c.md).
