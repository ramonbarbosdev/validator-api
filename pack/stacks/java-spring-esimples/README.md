# Stack overlay: Java Spring (e-Simples)

Extensão opcional para projetos com **tenant**, **financeiro**, **Padrão C** (listagem enxuta + filho).

**Fonte única:** edite padrões e-Simples **somente aqui** (`stacks/java-spring-esimples/`). O `esimples-api` não versiona `docs/padrao/` nem `docs/validador/` — só roda `install` na VPS ou no desktop (cópia local, `.gitignore` no app).

Instalação:

```bash
./install/install.sh /path/esimples-api java-spring-esimples
```

| Artefato | Destino no projeto |
|----------|-------------------|
| `docs/padrao/colecao-filha-vinculada-pai.md` | `docs/padrao/` |
| `docs/padrao/mestre-detalhe-conta-receber.md` | `docs/padrao/` |
| `docs/padrao/carga-faixa-manifest.json` | `docs/padrao/` |
| `docs/validador/revisao.overlay.md` | `docs/validador/revisao.overlay.md` |

No validador, usar `revisao.md` (genérico) + linhas em `revisao.overlay.md` para vizinhos (`ContaPagarService`, etc.).
