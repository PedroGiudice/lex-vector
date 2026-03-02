# Retomada: ccui-app -- Eliminar mocks e hardcoding, tornar funcional

## Contexto rapido

O ccui-app (Tauri 2 + React 19 + Tailwind 4) tem o redesign "Claude Terroso" implementado com 4 componentes visuais (CaseSelector, SessionView, ChatView, styles.css), agent tabs via WebSocket, split view TAB/SPLIT, e sidebar com lista de sessoes. O app builda, instala via .deb, conecta ao backend e funciona para o fluxo basico (selecionar caso, chat). Porem a maioria dos botoes/dados sao mock ou hardcoded. Esta sessao deve tornar o app funcional de verdade.

O contexto detalhado da sessao anterior esta em `docs/contexto/02032026-ccui-features-e-bugfix.md`.

## Arquivos principais

- `legal-workbench/ccui-app/src/components/SessionView.tsx` -- layout principal, sidebar, agent tabs, split view, status bar
- `legal-workbench/ccui-app/src/components/ChatView.tsx` -- mensagens user/assistant
- `legal-workbench/ccui-app/src/components/CaseSelector.tsx` -- tela de selecao de caso
- `legal-workbench/ccui-app/src/components/StartupGate.tsx` -- tunnel SSH automatico
- `legal-workbench/ccui-app/src/hooks/useAgents.ts` -- hook WebSocket para agentes
- `legal-workbench/ccui-app/src/hooks/useTauriStore.ts` -- wrapper Tauri store
- `legal-workbench/ccui-app/src/hooks/useCcuiApi.ts` -- fetch wrappers REST
- `legal-workbench/ccui-app/src/hooks/useChat.ts` -- hook de chat
- `legal-workbench/ccui-app/src/contexts/WebSocketContext.tsx` -- WS com reconnect
- `legal-workbench/ccui-app/src/types/protocol.ts` -- tipos do protocolo WS
- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS (fonte de verdade)
- `legal-workbench/ccui-backend/src/routes.rs` -- endpoints REST

## Proximos passos (por prioridade)

### 1. Eliminar dados hardcoded na status bar
**Onde:** `SessionView.tsx` linhas ~345-360
**O que:** "Opus 4.5" esta hardcoded -- deve consumir o campo `model` do evento `chat_init` do WebSocket. "main" (branch) esta hardcoded -- pode vir do backend ou ser removido. Contagem de agentes ja e dinamica (ok).
**Por que:** Informacoes falsas confundem o advogado
**Verificar:** Abrir sessao, status bar mostra modelo real da sessao

### 2. Tornar sidebar sessions interativa
**Onde:** `SessionView.tsx`, componente `SessionsList` (~linhas 103-155)
**O que:** Clicar numa sessao deve reconectar o WS aquela sessao (ou abrir em nova tab). Atualmente renderiza lista mas sem onClick.
**Por que:** Botao existe mas nao faz nada -- confuso para usuario
**Verificar:** Clicar em sessao ativa na sidebar muda o chat

### 3. File tree real
**Onde:** `SessionView.tsx`, componente `FileTree` (~linhas 158-188)
**O que:** Substituir placeholder estatico por dados reais. Backend pode servir via novo endpoint (GET /api/cases/{id}/files) ou o frontend pode listar via Tauri fs API se tiver acesso local. Decidir abordagem.
**Por que:** Advogado precisa ver documentos do caso
**Verificar:** File tree mostra arquivos reais do caso selecionado

### 4. Split panel com output real dos agentes
**Onde:** `SessionView.tsx`, componente `SplitPanel` (~linhas 191-220)
**O que:** Cada agente no painel split deve mostrar output real via WS (filtrar mensagens por channel/pane_id do agente). Atualmente mostra "Output do agente" placeholder.
**Por que:** Split view so tem utilidade se mostrar dados reais
**Verificar:** Iniciar sessao com team, split mostra output dos agentes secundarios

### 5. Sidebar busca e configuracoes
**Onde:** `SessionView.tsx`, tabs "search" e "settings"
**O que:** Busca: filtrar mensagens/sessoes por texto. Config: modelo preferido, tema, export de sessao.
**Por que:** Botoes existem na icon strip mas mostram "em breve"
**Verificar:** Busca filtra, config mostra opcoes reais

### 6. Error boundary global
**Onde:** `src/App.tsx` ou novo `ErrorBoundary.tsx`
**O que:** Envolver o app em React error boundary que mostra mensagem amigavel em vez de tela branca. O crash do session_id.slice so foi possivel porque nao havia boundary.
**Por que:** Qualquer erro de render derruba o app inteiro
**Verificar:** Simular erro em componente, boundary captura e mostra fallback

### 7. CaseSelector -- conectar filtros e stats reais
**Onde:** `CaseSelector.tsx`
**O que:** Filtros (Em andamento, Concluidos, Recentes) sao visuais mas nao filtram. Stats (TOTAL, EM ANDAMENTO, etc.) usam dados mock. Conectar ao GET /api/cases real.
**Por que:** Tela funciona para selecao basica mas dados sao falsos
**Verificar:** Filtros mudam lista, stats refletem dados reais

## Como verificar

```bash
cd legal-workbench/ccui-app

# Build frontend
PATH="/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH" bun run build

# Build Tauri (lembrar: CC=/usr/bin/gcc, beforeBuildCommand="" temporario)
CC=/usr/bin/gcc PATH="/home/opc/.bun/bin:/home/opc/.cargo/bin:/home/opc/.nvm/versions/node/v22.22.0/bin:/usr/bin:$PATH" cargo tauri build --bundles deb

# Transferir
scp src-tauri/target/release/bundle/deb/ccui-app_0.1.0_amd64.deb cmr-auto@100.102.249.9:~/Desktop/

# Backend (se precisar)
systemctl --user status ccui-backend  # ou cargo run no ccui-backend/

# Tauri MCP (debug remoto)
# driver_session start com host=100.102.249.9
# webview_execute_js, read_logs source=console, dom_snapshot
```

## Notas de ambiente

- `cc` aliasado para `claude` no zsh -- usar `CC=/usr/bin/gcc` antes de cargo build
- `beforeBuildCommand: "bun run build"` falha no cargo tauri build (bun nao no PATH do subprocess) -- esvaziar temporariamente ou buildar dist antes
- Node 22 nao esta no PATH default -- sempre prefixar com PATH="/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH"
- Tauri MCP bridge conecta via host 100.102.249.9 porta 9223
