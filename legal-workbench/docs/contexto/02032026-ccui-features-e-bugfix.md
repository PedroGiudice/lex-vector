# Contexto: ccui-app -- Features funcionais + bugfix crash

**Data:** 2026-03-02
**Sessao:** ccui-redesign-vibma (quarta sessao do dia)
**Duracao:** ~1.5h

---

## O que foi feito

### 1. Ambiente de build resolvido (Node 22)

Node 22.22.0 disponivel em `/home/opc/.nvm/versions/node/v22.22.0/bin/`. Build funciona:
```bash
PATH="/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH" bun run build
```
Problema anterior: Vite 7 exigia Node >= 20.19, VM tinha apenas Node 18.

### 2. MonaspiceAr Nerd Font Mono instalada

3 arquivos OTF (Regular, Bold, Italic) em `ccui-app/public/fonts/`. @font-face declarado no `styles.css`. CSS import order corrigido: Google Fonts ANTES do Tailwind import para evitar warning.

### 3. Hook useAgents (agent tabs reais)

Novo hook `src/hooks/useAgents.ts` consome eventos WebSocket:
- `agent_joined` (name, color, model, pane_id)
- `agent_left` (name)
- `agent_crashed` (name)

Protocolo TS em `src/types/protocol.ts` atualizado com esses 3 tipos. Fallback para `[{ name: "Main", color: "var(--agent-terracota)" }]` quando nenhum agente conectado.

### 4. Split view (WF-02)

Toggle TAB/SPLIT via `Ctrl+\`. Estado persistido via `useTauriStore`. No modo split:
- Chat principal ocupa flex-[7]
- Painel direito (320px = `--detail-panel`) mostra agentes secundarios empilhados
- Indicador "SPLIT" na status bar

### 5. Sidebar funcional

- Tab "sessoes": componente SessionsList faz GET /api/sessions via hook `useSessions`
- Tab "arquivos": componente FileTree mostra estrutura placeholder (base/, embeddings/, metadata/, CLAUDE.md) para o caseId ativo
- Tab "busca" e "config": placeholders

### 6. Correcoes Tauri (violacoes)

- `localStorage` substituido por `useTauriStore` (hook wrapper de `@tauri-apps/plugin-store` com fallback browser)
- `navigator.clipboard` substituido por `@tauri-apps/plugin-clipboard-manager`
- Permissoes `store:default` e `clipboard-manager:default` adicionadas ao capabilities
- Plugins registrados no `lib.rs`

### 7. Bugfix: crash ao abrir caso

**Causa raiz:** `SessionsList` renderiza `s.session_id.slice(0, 8)` sem optional chaining. Backend retornava sessoes onde `session_id` era undefined, crashando React inteiro (sem error boundary).

**Fix:** `s.session_id?.slice(0, 8) ?? "sessao"` no SessionView.tsx:146.

**Nota sobre build:** O `cargo tauri build` recompila Rust mas embeda o `dist/` do frontend. Se o dist nao foi rebuilado apos o fix, o binario sai com JS antigo. Fluxo correto:
1. `bun run build` (gera dist com fix)
2. `cargo tauri build --bundles deb` (embeda dist atualizado)

**Nota sobre ambiente:** `cc` esta aliasado para `claude` no zsh, quebrando o linker. Workaround: `CC=/usr/bin/gcc cargo build`.

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `ccui-app/src/styles.css` | Modificado -- @font-face MonaspiceAr + import order |
| `ccui-app/src/components/SessionView.tsx` | Reescrito -- agent tabs reais, split view, sidebar, fix crash |
| `ccui-app/src/hooks/useAgents.ts` | Criado -- hook WebSocket para agentes |
| `ccui-app/src/hooks/useTauriStore.ts` | Criado -- wrapper Tauri store com fallback |
| `ccui-app/src/types/protocol.ts` | Modificado -- agent_joined/left/crashed |
| `ccui-app/src/components/StartupGate.tsx` | Modificado -- clipboard plugin |
| `ccui-app/src-tauri/capabilities/default.json` | Modificado -- store + clipboard perms |
| `ccui-app/src-tauri/src/lib.rs` | Modificado -- plugins registrados |
| `ccui-app/src-tauri/Cargo.toml` | Modificado -- clipboard-manager dep |
| `ccui-app/public/fonts/` | Criado -- 3 OTF MonaspiceAr |

## Commits desta sessao

```
050ce1b fix(ccui-app): optional chaining em session_id, correcoes Tauri
32e77cf feat(ccui-app): agent tabs reais, split view, sidebar, MonaspiceAr font
```

## Pendencias criticas

1. **Botoes/elementos mock** -- maioria dos botoes nao faz nada (sidebar busca/config, file tree, etc.)
2. **Dados hardcoded na status bar** -- "Opus 4.5" e "main" sao strings literais, nao dados reais
3. **Status bar formatting** -- texto mostra "Opus 4.5" mas deveria ser "Opus 4.6" (modelo atual) e vir do backend
4. **Sidebar sessions** -- funcional mas sem interacao (clicar numa sessao nao faz nada)
5. **File tree** -- placeholder estatico, nao busca dados reais do backend
6. **Split panel** -- mostra "Output do agente" placeholder, nao consome output real
7. **Error boundary** -- React crasha inteiro em erros de render, precisa de boundary
8. **Build workflow** -- `cc` aliasado para claude quebra cargo build; beforeBuildCommand nao funciona no cargo tauri build (bun nao no PATH do subprocesso)

## Decisoes tomadas

- **useTauriStore com fallback** -- permite dev no browser sem Tauri, detecta `window.__TAURI__`
- **Agent tabs degracam gracefully** -- sem agentes WS, mostra tab "Main" unica
- **Split view persiste estado** -- layout mode salvo no Tauri store entre sessoes
