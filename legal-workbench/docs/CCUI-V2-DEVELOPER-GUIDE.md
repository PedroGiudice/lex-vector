# CCui V2 - Developer Guide

**Última atualização:** 2025-12-31
**Autor:** PGR + Claude Code
**Para:** LGP (onboarding)

---

## Visão Geral

CCui (Claude Code UI) é uma interface de chat integrada ao Legal Workbench que simula a experiência do Claude Code CLI em uma interface web.

### Stack Técnico

| Camada | Tecnologia |
|--------|------------|
| Frontend | React + TypeScript + MUI |
| Backend | FastAPI + WebSockets |
| Infra | Docker + Traefik |
| Comunicação | WebSocket (streaming) + HTTP POST |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              CCui V2 React Components                      │  │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────────────────────────┐ │  │
│  │  │Icon Rail│ │ Sidebar  │ │     Main Chat Area          │ │  │
│  │  │  (5)    │ │(Chats/   │ │  - Messages                 │ │  │
│  │  │         │ │Explorer) │ │  - Input Terminal           │ │  │
│  │  └─────────┘ └──────────┘ └─────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  useChatWebSocket Hook                                     │  │
│  │  - Conecta a ws://localhost/ws?token=dev-token            │  │
│  │  - Recebe tokens de streaming                              │  │
│  │  - Envia mensagens via POST /api/chat                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Traefik (porta 80)                          │
│  PathPrefix(/ws) ──────► api-ccui-ws:8005                       │
│  PathPrefix(/api/chat) ─► api-ccui-ws:8005                      │
│  PathPrefix(/) ─────────► frontend-react:3000                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              api-ccui-ws (FastAPI)                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ WebSocket /ws                                            │    │
│  │  - Aceita conexões com token                            │    │
│  │  - Envia tokens de streaming                            │    │
│  │  - Mantém session_data por client                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ POST /api/chat                                           │    │
│  │  - Recebe { message, token }                            │    │
│  │  - Gera resposta                                        │    │
│  │  - Faz streaming via WebSocket                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Arquivos

```
legal-workbench/
├── frontend/src/
│   ├── components/ccui-v2/           # Componentes React do CCui
│   │   ├── CCuiApp.tsx              # Container principal
│   │   ├── CCuiHeader.tsx           # Header com path e modelo
│   │   ├── CCuiIconRail.tsx         # Barra lateral com 5 ícones
│   │   ├── CCuiSidebar.tsx          # Sidebar (Chats/Explorer)
│   │   ├── CCuiChatArea.tsx         # Área principal de chat
│   │   ├── CCuiInputTerminal.tsx    # Input estilo terminal
│   │   ├── CCuiStatusBar.tsx        # Status bar inferior
│   │   ├── CCuiChatInterface.tsx    # Lógica de chat integrada
│   │   └── index.ts                 # Exports
│   │
│   ├── hooks/
│   │   ├── useChatWebSocket.ts      # Hook de WebSocket
│   │   └── useChatMessages.ts       # Hook de gerenciamento de msgs
│   │
│   └── pages/
│       └── CCuiV2Module.tsx         # Página/módulo do CCui
│
├── docker/services/ccui-ws/          # Backend WebSocket
│   ├── main.py                       # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
│
└── docs/
    ├── CCUI-V2-DEVELOPER-GUIDE.md   # Este arquivo
    └── e2e-tests/
        └── CCUI-V2-E2E-REPORT.md    # Relatório de testes
```

---

## Como Rodar

```bash
# 1. Subir ambiente completo
cd legal-workbench
docker compose up -d

# 2. Acessar CCui V2
http://localhost/ccui-v2

# 3. Ver logs do backend
docker compose logs -f api-ccui-ws

# 4. Rebuild após mudanças
docker compose build api-ccui-ws && docker compose up -d api-ccui-ws
docker compose build frontend-react && docker compose up -d frontend-react
```

---

## Fluxo de Mensagens

```
1. Usuário digita mensagem no CCuiInputTerminal
                    │
                    ▼
2. CCuiChatInterface chama api.post('/api/chat', { message, token })
                    │
                    ▼
3. Backend (main.py) recebe POST
   - Gera resposta com generate_response()
   - Encontra WebSocket do cliente pelo token
                    │
                    ▼
4. Backend envia tokens via WebSocket:
   { type: "token", content: "palavra " }
   { type: "token", content: "palavra " }
   ...
   { type: "done" }
                    │
                    ▼
5. useChatWebSocket acumula tokens e atualiza estado
                    │
                    ▼
6. CCuiChatArea renderiza mensagem completa
```

---

## Comandos Suportados

O backend responde a comandos especiais:

| Comando | Descrição |
|---------|-----------|
| `/help` | Lista comandos disponíveis |
| `/status` | Status da sessão |
| `/clear` | Limpa conversa |
| `/model` | Info do modelo atual |

---

## Issues Conhecidos

### 1. Problema de Proporções (P0)

**Descrição:** CCui dentro do shell do LW causa redundância de sidebars.

**Sintoma:** Sidebar do LW + Icon Rail + Sidebar CCui = ~350px ocupados

**Soluções propostas:**
- **A:** CCui em rota standalone (sem RootLayout)
- **B:** RootLayout colapsável quando CCui ativo
- **C:** Redesign CCui para layout compacto

### 2. Views Não Implementadas (P1)

| View | Status |
|------|--------|
| Chats | ✅ Funcional |
| Explorer | ✅ Funcional (mock) |
| Search | ❌ "View not implemented" |
| Controls | ❌ "View not implemented" |
| Theme | ❌ "View not implemented" |

### 3. Backend Mock (P2)

`generate_response()` é mock. Para produção:
- Integrar com Claude API
- Adicionar autenticação
- Implementar histórico persistente

---

## Próximos Passos Sugeridos

1. **Resolver proporções** - Escolher entre opções A, B ou C
2. **Implementar Search** - Grep-like search nos arquivos
3. **Implementar Theme** - Toggle dark/light mode
4. **Claude API real** - Substituir mock por chamadas reais
5. **Persistência** - Salvar histórico de chats

---

## Testes E2E

Relatório completo em: `docs/e2e-tests/CCUI-V2-E2E-REPORT.md`

Screenshots disponíveis:
- `ccui-v2-initial.png` - Estado inicial
- `ccui-v2-input-filled.png` - Input preenchido
- `ccui-v2-explorer-view.png` - Sidebar Explorer
- `ccui-v2-working.png` - Chat funcionando

---

## Referências

- **Design Reference:** Baseado no Claude Code CLI oficial
- **WebSocket Protocol:** Custom, token-based streaming
- **Traefik Config:** Ver `docker-compose.yml` labels

---

*Documento gerado para onboarding de LGP no projeto CCui V2*
