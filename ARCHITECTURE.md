# ARCHITECTURE.md - North Star

Plataforma de automacao juridica brasileira. Desktop-first.

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

---

## Decisoes Arquiteturais

### ADR-001: Tauri como framework desktop
App desktop em vez de web app. Tauri 2.x com React frontend e Rust backend.
Motivo: acesso nativo a filesystem, notificacoes, dialogs.

### ADR-002: tmux como runtime de sessoes
Cada sessao Claude Code roda dentro de um pane tmux gerenciado pelo backend.
Permite multiplas sessoes simultaneas, persistencia entre reconexoes, e streaming de output.

### ADR-003: Dados fora do repositorio
Dados juridicos em `~/juridico-data/`, nunca no Git.

### ADR-004: Bun para frontend, uv para Python
Bun para JS/TS (frontend, hooks). uv para Python (ferramentas).

---

## Stack Completa

| Tecnologia | Versao | Uso |
|------------|--------|-----|
| Rust | 1.70+ | stj-vec |
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
