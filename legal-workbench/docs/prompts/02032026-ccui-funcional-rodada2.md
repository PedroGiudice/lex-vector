# Retomada: ccui-app -- File tree, split panel, busca/config

## Contexto rapido

O ccui-app tem status bar dinamica (modelo real via WS), sidebar interativa (clicar muda sessao), error boundary global, CaseSelector com filtros e stats reais. Backend alinhado: sessions retorna objetos, cases retorna ISO 8601. 41 testes passando, clippy limpo, frontend builda.

O contexto detalhado esta em `docs/contexto/02032026-ccui-funcional-rodada2.md`.

## Arquivos principais

- `legal-workbench/ccui-app/src/components/SessionView.tsx` -- layout, sidebar, agent tabs, split view
- `legal-workbench/ccui-app/src/hooks/useSessionMeta.ts` -- model via chat_init WS
- `legal-workbench/ccui-app/src/hooks/useCcuiApi.ts` -- fetch wrappers REST (adaptados)
- `legal-workbench/ccui-app/src/hooks/useAgents.ts` -- hook WS para agentes
- `legal-workbench/ccui-app/src/hooks/useChat.ts` -- hook de chat (mensagens)
- `legal-workbench/ccui-app/src/contexts/WebSocketContext.tsx` -- WS com reconnect
- `legal-workbench/ccui-app/src/types/protocol.ts` -- tipos do protocolo WS
- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS (fonte de verdade)
- `legal-workbench/ccui-backend/src/routes.rs` -- endpoints REST

## Proximos passos (por prioridade)

### 1. File tree real
**Onde:** `SessionView.tsx`, componente `FileTree` (~linhas 160-197)
**O que:** Substituir placeholder estatico. Opcoes:
- (A) Novo endpoint backend GET /api/cases/{id}/files que lista arquivos do diretorio do caso
- (B) Tauri fs API para listar diretorio local (se o app tiver acesso)
**Decidir abordagem antes de implementar.**
**Verificar:** File tree mostra arquivos reais do caso selecionado

### 2. Split panel com output real dos agentes
**Onde:** `SessionView.tsx`, componente `SplitPanel` (~linhas 199-244)
**O que:** Cada agente no painel split deve mostrar output real. O hook `useAgents` ja captura `pane_id` por agente. Filtrar mensagens WS por canal/pane_id.
**Depende:** Backend ja envia `output` com `channel` -- precisa mapear channel -> pane_id -> agente.
**Verificar:** Iniciar sessao com team, split mostra output dos agentes secundarios

### 3. Sidebar busca
**Onde:** `SessionView.tsx`, tab "search"
**O que:** Filtrar mensagens da sessao atual por texto. Input de busca + lista de resultados com highlight.
**Verificar:** Digitar texto filtra mensagens do chat

### 4. Sidebar configuracoes
**Onde:** `SessionView.tsx`, tab "settings"
**O que:** Opcoes basicas: tema (dark only por ora), export de sessao (JSON/markdown), modelo preferido.
**Verificar:** Config mostra opcoes, export gera arquivo

### 5. Testes WS (investigar)
**Onde:** `tests/routes_integration.rs`
**O que:** 4 testes WS travam indefinidamente. Provavel causa: dependem de Claude CLI binario disponivel e funcional. Investigar se podem ser mockados ou marcados como `#[ignore]`.
**Verificar:** `cargo test -- --test-threads=1` nao trava

## Como verificar

```bash
cd legal-workbench/ccui-app

# Build frontend
PATH="/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH" bun run build

# Build Tauri
CC=/usr/bin/gcc PATH="/home/opc/.bun/bin:/home/opc/.cargo/bin:/home/opc/.nvm/versions/node/v22.22.0/bin:/usr/bin:$PATH" cargo tauri build --bundles deb

# Backend tests (excluir WS que travam)
cd ../ccui-backend
cargo test --test config_error_unit --test session_integration --test session_persistence -- --test-threads=1
cargo test --test routes_integration -- --test-threads=1 sessions_empty health list_cases channels not_found
cargo clippy -- -W clippy::pedantic
```
