# Importante — consumidor da API (front)

Comportamento incorreto com evidência; usuário não conclui fluxo ou tela quebra **sem** ser falha de segurança nível Crítico.

| Padrão | Evidência no diff | Impacto para o usuário |
|--------|-------------------|-------------------------|
| Contrato HTTP quebra fluxo | Login sem cookie; token mascarado sem `Set-Cookie`; refresh sem distinguir renovação (ex. sempre 204) | Não entra no app; nome/org não carrega |
| 401/403 trocados | Sem permissão → `SESSION_EXPIRED` | Logout em vez de “sem acesso” |
| Bootstrap impossível | `/me`/refresh bloqueados em 2FA/troca senha sem rota alternativa | Trava na login/seleção de org |
| Validação não impede persistência inválida | POST aceito; falha depois | 500 ou dado inconsistente |
| Regressão em método compartilhado | Chamadores quebram (Grep) | Telas quebram após deploy da API |
| SPEC/aceite não atendido | Critério na SPEC vs diff | Funcionalidade não aparece |
| Whitelist/legado | `EV-VAL-004` | Não salva cadastro antigo |
| Colisão REST | `EV-REST-006/007` | URL errada (404/500) |
| Cookie homolog | `secure`/`domain`/`path` incoerente **se** aceite inclui homolog | Login falha em ambiente |

## Evidência

Regra ou doc, arquivo/trecho, entrada → resultado errado, impacto.

Polish de mensagem com fluxo OK → [`../melhoria-ajuste/consumidor-api.md`](../melhoria-ajuste/consumidor-api.md).
