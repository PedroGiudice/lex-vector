# Contexto: ccui-app -- Motion, reconnect_session e docs reescritos

**Data:** 2026-03-04
**Sessao:** ccui-redesign-vibma (continuacao da sessao de session mgmt)

---

## O que foi feito

### 1. reconnect_session no backend (Rust)

Implementado mecanismo completo de reconexao a sessoes existentes no ccui-backend.

**ws.rs:**
- `ClientMessage::ReconnectSession { session_id }` -- novo tipo de mensagem WS
- `ServerMessage::SessionReconnected { session_id, case_id, name }` -- resposta

**routes.rs -- handle_client_message_tracked:**
- Trata `ReconnectSession`: verifica se sessao existe no SessionManager, verifica se tmux esta vivo via `is_session_alive`, re-spawna Claude se necessario
- Retorna `SessionReconnected` ou erro

**session.rs:**
- `is_session_alive(&self, session_id) -> bool` -- verifica se pane tmux existe
- `cleanup_dead_sessions(&self)` -- remove sessoes zumbi cujo tmux morreu

**routes_integration.rs:** 2 testes novos (reconnect valido + reconnect inexistente). 15 testes totais passando, clippy pedantic limpo.

### 2. reconnect_session no frontend (React)

O frontend ja tinha os tipos e handlers implementados de sessao anterior:
- `protocol.ts`: tipos `reconnect_session` e `session_reconnected`
- `SessionContext.tsx`: `reconnectSession()` envia via WS, handler atualiza estado
- `SessionView.tsx`: `handleSwitchSession` usa reconnect em vez de destroy+create

### 3. Motion e feedback visual

**ApertureSpinner.tsx** (novo arquivo):
- `ApertureSpinner` -- spinner Canvas 2D puro (abertura de camera, morphing quadrado->circulo, rotacao lenta). Paleta adaptada ao design system terroso do app.
- `ApertureSpinnerMini` -- variante compacta (20px default), sem connector lines, para uso inline.

**Spinners.tsx** reescrito:
- ReactorSpinner e PhyllotaxisSpinner agora sao re-exports do ApertureSpinner (compatibilidade)
- Todo codigo p5.js removido (useP5, window.p5, etc.)
- p5.js CDN (~800kb) removido do index.html

**ChatView.tsx:**
- `StreamingIndicator` usa `ApertureSpinnerMini` (20px) + texto "Pensando..."
- Aparece abaixo da ultima mensagem quando Claude esta processando
- Participa do scroll normalmente

**AppRouter.tsx:**
- Crossfade de 200ms entre CaseSelector e SessionView (CSS transitions, sem framer-motion)

**SessionView.tsx:**
- Sidebar permanece no DOM (sem condicional `&&`), anima com `translateX` + opacity (150ms)
- Split panel com transicao equivalente

### 4. Docs reescritos

**CLAUDE.md (raiz):** De 167 para 91 linhas. Removidas duplicatas de regras globais (~/.claude/), referencias fantasma (DISASTER_HISTORY.md que nao existe), secoes genericas. Mantido: erros aprendidos, team, estrutura atualizada.

**ARCHITECTURE.md:** Reescrito completamente. ccui-app como produto principal, stack com versoes corretas (Tauri 2.3, React 19, Vite 6, axum 0.8), ADRs relevantes (Tauri, tmux, dados fora do repo, Bun/uv). Removidas referencias fantasma (infra/, path_utils.py, adk-agents migrados).

### 5. Remocao do adk-agents (feita pelo usuario)

Diretorio `adk-agents/` removido do repositorio. Nao deve ser mencionado em docs.

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `CLAUDE.md` | Reescrito -- enxugado, sem duplicatas |
| `ARCHITECTURE.md` | Reescrito -- estado atual real |
| `ccui-app/src/components/ApertureSpinner.tsx` | Criado -- spinner Canvas 2D |
| `ccui-app/src/components/Spinners.tsx` | Reescrito -- re-exports, p5.js removido |
| `ccui-app/src/components/ChatView.tsx` | Modificado -- StreamingIndicator com ApertureSpinnerMini |
| `ccui-app/src/components/AppRouter.tsx` | Modificado -- crossfade 200ms |
| `ccui-app/src/components/SessionView.tsx` | Modificado -- sidebar/split transicoes |
| `ccui-app/src/contexts/SessionContext.tsx` | Modificado -- reconnectSession |
| `ccui-app/src/types/protocol.ts` | Modificado -- tipos reconnect |
| `ccui-backend/src/ws.rs` | Modificado -- ReconnectSession/SessionReconnected |
| `ccui-backend/src/routes.rs` | Modificado -- handler reconnect |
| `ccui-backend/src/session.rs` | Modificado -- is_session_alive, cleanup_dead |
| `ccui-backend/tests/routes_integration.rs` | Modificado -- 2 testes reconnect |

## Commits desta sessao

```
e72df21 docs: reescrever CLAUDE.md e ARCHITECTURE.md com estado atual
a6dea07 feat(ccui-app): motion, ApertureSpinner e reconnect_session frontend
071c2f9 feat(ccui-backend): implementar reconnect_session no protocolo WS
```

## Bugs conhecidos (NAO resolvidos)

### BUG 1: Sessoes zumbi acumulam
Backend agora tem `cleanup_dead_sessions()` mas nao e chamado automaticamente. Precisa ser invocado periodicamente ou no startup.

### BUG 2: Backend em producao desatualizado
O backend rodando na porta 8005 ainda e versao antiga. Precisa recompilar e reiniciar.

### BUG 3: Build do app nao foi testada
As mudancas de motion e spinners nao foram compiladas em .deb nem testadas no PC Linux. Build pode ter problemas.

## Decisoes tomadas

- **NAO instalar framer-motion:** CSS moderno (@starting-style, transitions) + hook utilitario cobre os casos de uso. Zero deps novas.
- **Substituir p5.js por Canvas 2D puro:** Remove 800kb de CDN, elimina dependencia externa, app funciona 100% offline.
- **ApertureSpinner como spinner principal:** Paleta terrosa alinha com redesign editorial, visual sofisticado (abertura de camera).
- **Motion apenas onde comunica estado:** Transicoes de tela, sidebar, indicador de processamento. Sem animacao em mensagens do chat.
- **CLAUDE.md nao duplica regras globais:** Regras comuns ficam em ~/.claude/CLAUDE.md e rules/*.md.
