# Plano: Redesign Frontend claudecodeui-main → Estilo adk-gui

**Data:** 2025-12-20
**Objetivo:** Substituir o frontend atual do claudecodeui-main pelo layout terminal-style do copy-of-adk-gui, mantendo toda funcionalidade backend.

---

## Contexto

### Atual (claudecodeui-main)
- Project selector como tela inicial
- Sidebar de projetos
- Tema azul escuro
- Sem histórico de conversas visível
- Sem status bar

### Desejado (copy-of-adk-gui style)
- Chat direto como tela principal
- Sidebar com **histórico de conversas** (TODAY, YESTERDAY, PREVIOUS 7 DAYS)
- Tema **preto puro (#000000)** + accent **coral (#d97757)**
- Status bar (READY/BUSY, ctx%, UTF-8, tempo)
- Icon rail (Chat, Files, Search, Git, Debug, Settings)

---

## Arquivos de Referência

- **Layout desejado:** `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/copy-of-adk-gui (1)/App.tsx`
- **Backend atual:** `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/claudecodeui-main/server/`
- **Frontend atual:** `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/claudecodeui-main/src/App.jsx`

---

## Fases de Implementação

### Fase 1: Preparação (15 min)
- [ ] Backup do App.jsx atual
- [ ] Analisar endpoints do backend que precisam ser conectados
- [ ] Identificar componentes reutilizáveis do claudecodeui-main

### Fase 2: Design System (30 min)
- [ ] Atualizar `tailwind.config.js` com cores do adk-gui
- [ ] Atualizar `index.css` com estilos globais (scrollbar, animações)
- [ ] Adicionar Prism.js ao `index.html` para syntax highlighting

### Fase 3: Componentes Core (1h)
- [ ] `CCuiHeader.jsx` - Header com botões macOS, path, modelo
- [ ] `CCuiIconRail.jsx` - Barra lateral de ícones
- [ ] `CCuiSidebar.jsx` - Sidebar com histórico de conversas
- [ ] `CCuiStatusBar.jsx` - Status bar inferior
- [ ] `CCuiCodeBlock.jsx` - Bloco de código com syntax highlighting
- [ ] `CCuiThinkingBlock.jsx` - Bloco de pensamento colapsável
- [ ] `CCuiChatInput.jsx` - Input terminal-style
- [ ] `CCuiMessage.jsx` - Componente de mensagem

### Fase 4: Integração Backend (1h)
- [ ] Conectar WebSocket existente (`/api/chat`)
- [ ] Conectar API de sessions (`/api/sessions`)
- [ ] Conectar API de projetos (`/api/projects`)
- [ ] Implementar streaming de mensagens
- [ ] Implementar histórico de conversas real

### Fase 5: App Principal (30 min)
- [ ] Reescrever `App.jsx` usando os novos componentes
- [ ] Manter roteamento existente (se houver)
- [ ] Testar fluxo completo

### Fase 6: Polish (15 min)
- [ ] Testar em diferentes tamanhos de tela
- [ ] Ajustar animações
- [ ] Verificar performance
- [ ] Build final

---

## Mapeamento Backend → Frontend

| Backend Endpoint | Uso no Frontend |
|------------------|-----------------|
| `WS /api/chat` | Streaming de mensagens |
| `GET /api/sessions` | Lista de histórico de conversas |
| `POST /api/sessions` | Criar nova conversa |
| `GET /api/projects` | Lista de projetos |
| `GET /api/settings` | Configurações do usuário |

---

## Componentes a Preservar do claudecodeui-main

- `contexts/AuthContext.jsx` - Autenticação
- `contexts/WebSocketContext.jsx` - WebSocket
- `hooks/useLocalStorage.jsx` - Storage
- `utils/api.js` - API helpers

---

## Subagentes Recomendados

1. **frontend-developer** - Para criar os componentes React
2. **tui-designer** - Para o CSS/Tailwind (estilo terminal)
3. **code-reviewer** - Para revisar a integração final

---

## Critérios de Sucesso

- [ ] Layout idêntico ao screenshot do adk-gui
- [ ] Histórico de conversas funcional (TODAY, YESTERDAY, etc.)
- [ ] Status bar mostrando estado real (READY/BUSY, ctx%)
- [ ] Streaming de mensagens funcionando
- [ ] Syntax highlighting em code blocks
- [ ] Responsivo (desktop e mobile)
- [ ] Build sem erros
