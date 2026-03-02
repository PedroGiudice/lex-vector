# Contexto: ccui-app -- Tornar funcional (rodada 2)

**Data:** 2026-03-02
**Sessao:** ccui-redesign-vibma (quinta sessao do dia)

---

## O que foi feito

### 1. Status bar dinamica (SessionView)

Hook `useSessionMeta` criado (`src/hooks/useSessionMeta.ts`) -- escuta evento WS `chat_init` e expoe `{ model, claudeSessionId }`. Status bar agora mostra modelo real da sessao em vez de "Opus 4.5" hardcoded. Bloco GitBranch/"main" removido (sem fonte de dados).

### 2. Sidebar sessions interativa (SessionView)

Componente `SessionsList` recebe `currentSessionId` e `onSwitchSession(caseId)`. Clicar numa sessao:
1. Envia `destroy_session` para sessao atual
2. Chama `createSession` com novo case_id
Sessao ativa destacada com borda accent.

### 3. Error boundary global

Novo `src/components/ErrorBoundary.tsx` (class component). Fallback amigavel com botoes "Recarregar" e "Tentar novamente". `App.tsx` envolvido pelo boundary.

### 4. CaseSelector filtros e stats reais

- Filtro "Recentes": casos com `last_modified` nos ultimos 7 dias
- Busca expandida: pesquisa em `id`, `title` e `parties`
- Stat "ULTIMA ATIVIDADE": calcula `last_modified` mais recente entre todos os casos

### 5. Alinhamento backend/frontend (endpoints REST)

**GET /api/sessions:** retorna objetos `{ session_id, case_id, created_at }` em vez de array de strings. Frontend `useSessions` aceita ambos formatos com fallback.

**GET /api/cases:** `last_modified` agora e ISO 8601 (`chrono::to_rfc3339()`) em vez de Unix timestamp. Frontend `useCases` normaliza: converte number para ISO string se necessario.

**SessionInfo:** novo campo `created_at: Option<String>` populado na criacao.

### 6. Fix race condition em testes session_persistence

`sessions_dir` era hardcoded `/tmp/ccui-sessions` -- testes compartilhavam diretorio. Adicionado campo `sessions_dir` ao `AppConfig`. Testes usam tempdir isolado. 6/6 passando.

## Commits desta sessao

```
f270229 fix(ccui-backend): sessions_dir configuravel, corrige race condition em testes
4aa76d5 fix(ccui): alinhar formato de dados entre backend e frontend
d971052 feat(ccui-app): status bar dinamica, sidebar interativa, error boundary, filtros CaseSelector
```

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `ccui-app/src/components/SessionView.tsx` | Modificado -- status bar dinamica, sidebar onClick |
| `ccui-app/src/components/CaseSelector.tsx` | Modificado -- filtros, busca, stats |
| `ccui-app/src/components/ErrorBoundary.tsx` | Criado -- error boundary global |
| `ccui-app/src/hooks/useSessionMeta.ts` | Criado -- hook chat_init WS |
| `ccui-app/src/hooks/useCcuiApi.ts` | Modificado -- adapta formatos backend |
| `ccui-app/src/hooks/useTauriStore.ts` | Tracked -- wrapper Tauri store |
| `ccui-app/src/App.tsx` | Modificado -- ErrorBoundary wrapper |
| `ccui-backend/src/routes.rs` | Modificado -- sessions objetos, cases ISO 8601 |
| `ccui-backend/src/session.rs` | Modificado -- created_at, sessions_dir |
| `ccui-backend/src/config.rs` | Modificado -- sessions_dir campo |
| `ccui-backend/tests/session_persistence.rs` | Modificado -- tempdir isolado |

## Pendencias restantes (do prompt original)

1. **File tree real** (tarefa 3) -- placeholder estatico, precisa endpoint backend ou Tauri fs
2. **Split panel com output real** (tarefa 4) -- mostra "Output do agente", precisa filtrar WS por pane_id
3. **Sidebar busca e config** (tarefa 5) -- placeholders "em breve"
4. **Testes WS** -- `ws_create_and_destroy_session` e 3 outros testes WS travam (dependem de Claude CLI rodando)
5. **Build e deploy** -- frontend buildado mas nao deployado como .deb
