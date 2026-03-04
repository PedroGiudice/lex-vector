# ARCHITECTURE.md - North Star

Plataforma de automacao juridica brasileira. Desktop-first.

---

## Foco: App Desktop Tauri (CCUI)

O produto principal e o **app desktop Tauri** (`ccui-app`), que wrapa o Claude Code CLI
fornecendo interface grafica para advogados gerenciarem sessoes de analise juridica.

| Componente | Prioridade | Descricao |
|------------|------------|-----------|
| **ccui-app** | PRINCIPAL | Desktop app Tauri (Windows/Linux) |
| **ccui-backend** | PRINCIPAL | Backend Rust que gerencia sessoes via tmux |
| ferramentas/ | SUPORTE | Python tools (LTE, etc) |
| Docker | DEV/TEST | Ambiente de desenvolvimento |

---

## Arquitetura do Sistema

```
ccui-app (Tauri)
    |
    +-- React 19 SPA (Vite 6, Tailwind 4)
    |
    +-- WebSocket --> ccui-backend (:8005)
    |                    |
    |                    +-- tmux sessions --> Claude Code CLI
    |                    +-- REST API (sessions, cases, files)
    |
    +-- Tauri IPC --> Rust commands (list_case_files, etc)
    +-- Tauri plugins (fs, dialog, notification)
```

### ccui-app (Frontend Desktop)

| Tecnologia | Versao |
|------------|--------|
| Tauri | 2.3.1 |
| React | 19.0.0 |
| Vite | 6.1.0 |
| Tailwind CSS | 4.0.6 |
| TypeScript | 5.7.3 |

Componentes principais:
- `SessionView` -- vista principal com chat, sidebar de sessoes, file tree
- `CaseSelector` -- selecao de caso juridico
- `ChatView` -- renderizacao de output do Claude
- `SessionsList` -- lista de sessoes com rename inline e delete
- Contexts: `WebSocketContext`, `SessionContext`
- Hooks: `useCcuiApi`, `useChat`, `useAgents`, `useTauriStore`

### ccui-backend (Backend Rust)

| Tecnologia | Versao |
|------------|--------|
| axum | 0.8.1 |
| tokio | 1.x (full) |
| tower-http | 0.6 (CORS) |
| chrono | 0.4 |

Endpoints:
- `GET /health`
- `GET /api/sessions` -- lista sessoes (com name, case_id, created_at)
- `GET /api/sessions/:id`
- `POST /api/sessions` -- cria sessao
- `PATCH /api/sessions/:id` -- rename
- `DELETE /api/sessions/:id` -- destroi sessao + tmux
- `POST /api/sessions/:id/input` -- envia input
- `POST /api/sessions/:id/interrupt` -- Ctrl+C
- `GET /api/sessions/:id/output` -- streaming output
- `GET /api/sessions/:id/channels` -- canais ativos
- `GET /api/cases` -- lista casos disponiveis
- `GET /ws` -- WebSocket (create_session, reconnect_session, send_input, destroy_session)

7 arquivos de teste (unit + integration). Clippy pedantic limpo.

---

## Principios Fundamentais

### 1. Separacao de Camadas

| Camada | Local | Git |
|--------|-------|-----|
| Codigo | `lex-vector/` | Sim |
| Ambiente | `.venv/`, `node_modules/` | Nunca |
| Dados juridicos | `~/juridico-data/` | Nunca |

### 2. Desktop-First

O produto e um app desktop. Docker e servicos web sao infraestrutura de suporte,
nao o produto final. Decisoes de UX priorizam a experiencia desktop.

### 3. Uma Unica Arquitetura

Nunca manter duas arquiteturas concomitantemente. Um app, um backend, uma fonte de verdade.
O frontend Next.js (`frontend/`) e legado -- substituido por `ccui-app`.

---

## Decisoes Arquiteturais

### ADR-001: Tauri como framework desktop
App desktop em vez de web app. Tauri 2.x com React frontend e Rust backend.
Motivo: acesso nativo a filesystem, notificacoes, dialogs.

### ADR-002: tmux como runtime de sessoes
Cada sessao Claude Code roda dentro de um pane tmux gerenciado pelo ccui-backend.
Permite multiplas sessoes simultaneas, persistencia entre reconexoes, e streaming de output.

### ADR-003: Dados fora do repositorio
Dados juridicos em `~/juridico-data/`, nunca no Git.

### ADR-004: Bun para frontend, uv para Python
Bun para JS/TS (frontend, hooks). uv para Python (ferramentas).

---

## Stack Completa

| Tecnologia | Versao | Uso |
|------------|--------|-----|
| Tauri | 2.3.1 | Framework desktop (PRINCIPAL) |
| Rust | 1.70+ | ccui-backend, Tauri backend, stj-vec |
| React | 19.0.0 | Frontend SPA |
| Vite | 6.1.0 | Build tool |
| Tailwind CSS | 4.0.6 | Styling |
| TypeScript | 5.7.3 | Frontend |
| axum | 0.8.1 | HTTP server (ccui-backend) |
| tokio | 1.x | Async runtime |
| Python | 3.12 | Ferramentas (LTE) |
| Marker | - | PDF extraction (deep learning) |
| Bun | 1.x | Package manager, JS runtime |
| Docker | 24+ | Containerizacao (dev) |

---

## Restricoes

| Acao | Status |
|------|--------|
| Python sem venv | BLOQUEADO |
| .venv / node_modules no Git | BLOQUEADO |
| npm/yarn em vez de Bun | BLOQUEADO |
| pip em vez de uv | BLOQUEADO |
| Emojis em qualquer output | BLOQUEADO |

---

*Ultima atualizacao: 2026-03-04*
