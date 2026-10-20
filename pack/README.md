# Pacote validador (Cursor)

Regras `EV-*`, skill `/api-validator`, `docs/`, `install/` e stacks — embutido no **validator-api**.

- Instalar no repo da API: `install/install.ps1` ou `install.sh` (alvo = raiz do projeto Java).
- Stack e-Simples (opcional): `java-spring-esimples`.
- CI/agente: `scripts/ci-api-validator.py`.

Em produção (Docker), `CURSOR_API_VALIDATOR_ROOT` aponta para `/app/pack` na imagem.
