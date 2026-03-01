# Contexto: Design do CCUI Multi-Agent Teams Frontend

**Data:** 2026-03-01
**Sessao:** wrapper-legal-agents-front (continuacao)
**Duracao:** ~1h

---

## O que foi feito

### 1. Merge da branch wrapper-legal-agents-front na main

Branch continha: redesign terroso do CCUI (paleta terracota/mogno/cafe), fixes do ccui-app
(protocol sync, chat_input, MCP bridge), e documentacao de sessoes anteriores.
Merge feito com `--no-ff`. Conflito menor com arquivo untracked resolvido via stash.

### 2. Brainstorming do novo frontend multi-agent

Sessao de design seguindo skill brainstorming com 5 perguntas de clarificacao.
Todas as decisoes de design foram tomadas e a abordagem arquitetural escolhida.

### 3. Tentativa de usar Vibma MCP

O Vibma MCP server esta instalado globalmente (logs existem em `~/.cache/claude-cli-nodejs/*/mcp-logs-Vibma/`),
porem as tools `mcp__Vibma__*` nao carregaram como funcoes disponiveis nesta sessao.
Motivo provavel: configuracao do MCP server precisa estar acessivel no startup da sessao.
O `mcpServers` em `~/.claude/settings.json` esta como array vazio `[]`.

Verificar: onde a configuracao Vibma esta definida e garantir que carregue na proxima sessao.

## Decisoes de design -- CCUI Multi-Agent Teams

Todas validadas com o usuario:

| Decisao | Escolha |
|---------|---------|
| Modo de visualizacao | **Dual**: tabs (um agente por vez) OU split (todos visiveis), usuario escolhe |
| Interacao com agentes | **Default main**, clicar no pane para interagir com teammate (como tmux) |
| Nivel de detalhe | **Modo cliente** (estruturado) ou **modo dev** (raw), toggle por usuario |
| Layout split | **Main ~70% + teammates em strip lateral direita**, panes redimensionaveis |
| Identidade visual | **Cores automaticas** da paleta terrosa por agente |
| Ferramenta de design | **Vibma** como referencia e documentacao |

### Abordagem arquitetural escolhida: Multi-Pane com State Centralizado

- Um unico WebSocket multiplexado (ja implementado no backend)
- Zustand store com `TeamState` espelhando o backend
- Componente `AgentPane` reutilizavel (mesmo para main e teammates)
- Layout manager controla disposicao (tabs vs split vs resize)
- Backend ja tem: `AgentJoined`, `AgentLeft`, `ChannelUpdate`, `AgentStatusChanged`, `TeamStateUpdate`

Abordagens descartadas:
- Multiplos WebSockets (nao aproveita protocolo existente)
- Iframe-based (over-engineering)
- Timeline unificada (confuso, descartado pelo usuario)

## Estado dos arquivos

Nenhum arquivo editado nesta sessao (apenas merge de commits anteriores).

### Commits desta sessao (na main)

```
9d21f5d docs: contexto e prompts de sessoes anteriores (penpot, parsing debate)
2c79588 merge: wrapper-legal-agents-front (ccui-app + redesign terroso)
```

## Backend: estruturas existentes para agent teams

O ccui-backend (Rust/axum) ja tem:

```rust
// state.rs
pub struct Agent { id, name, status, channels: Vec<AgentChannel>, pane_id }
pub struct AgentChannel { id, name, output: String, channel_type: ChannelType }
pub struct TeamState { agents: HashMap<String, Agent>, active_team, version }

// websocket.rs
pub enum WebSocketMessage {
    AgentJoined { agent_id, agent_name, channels },
    AgentLeft { agent_id },
    AgentStatusChanged { agent_id, status },
    ChannelUpdate { agent_id, channel_id, output },
    TeamStateUpdate { agents, version },
}
```

O `TeamWatcher` faz polling a cada 500ms em `/tmp/agents`.
O `PaneProxy` mapeia panes tmux para agentes via `AGENT_ID=` no conteudo.
**Nota:** muitos TODOs no backend -- scan_agents e broadcast ainda nao implementados.

## Pendencias identificadas

1. **Vibma MCP nao funcional** -- tools nao carregam. Verificar configuracao global
2. **Design doc pendente** -- decisoes tomadas mas nao formalizadas em `docs/plans/`
3. **Backend incompleto** -- team_watcher.scan_agents e broadcast no main.rs sao TODOs
4. **Penpot desatualizado** -- Design System ainda usa paleta antiga (coral), telas vazias
