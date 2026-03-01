# Retomada: CCUI Multi-Agent Teams Frontend

## Contexto rapido

Fizemos brainstorming completo para o novo frontend do CCUI que mostra agent teams
(multiplos agentes simultaneos). Decisoes tomadas: modo dual (tabs + split),
interacao default com main mas clicavel para teammates, panes redimensionaveis,
cores automaticas por agente, layout main 70% + strip lateral.

A abordagem escolhida e **Multi-Pane com State Centralizado** -- um WebSocket
multiplexado, Zustand store com TeamState, componente AgentPane reutilizavel.
O backend Rust ja tem as structs e enum de mensagens WS, mas scan_agents e
broadcast ainda sao TODOs.

A intencao era usar **Vibma MCP** para criar o design antes de codar, mas as
tools nao carregaram nesta sessao. Prioridade 1: resolver Vibma e criar o design.

## Arquivos principais

- `legal-workbench/ccui-backend/src/state.rs` -- Agent, AgentChannel, TeamState
- `legal-workbench/ccui-backend/src/handlers/websocket.rs` -- WebSocketMessage enum
- `legal-workbench/ccui-backend/src/team_watcher.rs` -- TeamWatcher (polling)
- `legal-workbench/ccui-backend/src/pane_proxy.rs` -- PaneProxy (tmux interface)
- `legal-workbench/frontend/src/components/ccui-v2/` -- frontend atual (single-agent)
- `docs/contexto/01032026-ccui-agent-teams-design.md` -- contexto detalhado desta sessao

## Proximos passos (por prioridade)

### 1. Resolver Vibma MCP
**Onde:** configuracao global do Claude Code (MCP servers)
**O que:** garantir que `mcp__Vibma__*` tools carreguem na sessao
**Por que:** design-first com Vibma e a intencao declarada
**Verificar:** na nova sessao, tentar `mcp__Vibma__design_strategy` ou listar tools Vibma

### 2. Criar design no Vibma/Penpot
**Onde:** Vibma (referencia) + Penpot (documentacao)
**O que:** wireframes dos 3 modos: tab view, split view, transition entre ambos
**Por que:** design como referencia antes de codar
**Verificar:** export visual dos wireframes

### 3. Formalizar design doc com writing-plans
**Onde:** `docs/plans/YYYY-MM-DD-ccui-multi-agent.md`
**O que:** plano de implementacao baseado nas decisoes + design visual
**Por que:** guiar implementacao passo a passo
**Verificar:** doc existe e cobre componentes, state, layout, WS integration

### 4. Implementar frontend multi-agent
**Onde:** `legal-workbench/frontend/src/components/ccui-v2/`
**O que:** AgentPane, TeamStore (Zustand), LayoutManager, TabBar
**Por que:** feature principal desta branch
**Verificar:** `cd legal-workbench/frontend && bun run build`

### 5. Completar backend (TODOs)
**Onde:** `legal-workbench/ccui-backend/src/team_watcher.rs` e `main.rs`
**O que:** implementar scan_agents real e broadcast via WebSocket
**Por que:** frontend precisa de dados reais dos agentes
**Verificar:** `cd legal-workbench/ccui-backend && cargo test`

## Decisoes ja tomadas (NAO rediscutir)

- Modo dual tabs+split, usuario escolhe
- Default main, click para interagir com teammate
- Modo cliente (filtrado) e modo dev (raw), toggle
- Main 70% + strip lateral, redimensionavel
- Cores automaticas por agente (paleta terrosa)
- Abordagem: Multi-Pane com State Centralizado (WS multiplexado, Zustand)
- Timeline unificada DESCARTADA (confuso)

## Como verificar

```bash
# Frontend build
cd legal-workbench/frontend && bun run build

# Backend build
cd legal-workbench/ccui-backend && cargo build

# Verificar Vibma MCP
# Na nova sessao, checar se tools mcp__Vibma__* estao disponiveis
```
