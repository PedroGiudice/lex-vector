# Retomada: ccui-app -- Correcoes de Output/Input e Finalizacao

## Contexto rapido

O ccui-app (app Tauri standalone para advogados) foi implementado nesta sessao via agent team: scaffold Rust, tipos/contextos TypeScript, componentes React (CaseSelector, SessionView, ChannelTabs, TerminalPane), 30 testes, polish visual. O app compila (`cargo tauri build`), abre, conecta ao backend via tunnel SSH, e lista casos.

Dois problemas criticos foram identificados no primeiro teste real:
1. **Output ilegivel** -- TerminalPane mostra texto cru do tmux com ANSI mal-stripped (palavras grudadas)
2. **Input nao funciona** -- usuario nao consegue digitar e enviar comandos ao Claude Code

Dois teammates opus foram despachados para corrigir (podem ter terminado). O repo ADK-sandboxed-legal (clonado em /tmp/adk-ref/) tem padrao de referencia para wrapping de output.

## Documento de contexto

**LEIA PRIMEIRO:** `docs/contexto/27022026-ccui-app-implementation.md`

## Arquivos principais

- `legal-workbench/ccui-app/` -- app Tauri completo (React + Rust)
- `legal-workbench/ccui-app/src/components/TerminalPane.tsx` -- output (PRECISA REESCRITA)
- `legal-workbench/ccui-app/src/components/SessionView.tsx` -- input (PRECISA FIX)
- `legal-workbench/ccui-app/src/components/StartupGate.tsx` -- tunnel SSH automatico
- `legal-workbench/ccui-app/src-tauri/src/lib.rs` -- Tauri commands Rust
- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS (fonte de verdade)
- `legal-workbench/ccui-backend/src/pane_proxy.rs` -- como backend encaminha input ao tmux
- `legal-workbench/docs/plans/2026-02-27-ccui-app-standalone-design.md` -- design doc
- `/tmp/adk-ref/` -- repo de referencia para output wrapping (pode precisar re-clonar)

## Proximos passos (por prioridade)

### 1. Integrar resultado dos teammates opus (output + input)
**Onde:** worktrees dos teammates (verificar se concluiram)
**O que:** Mergear as correcoes de TerminalPane e SessionView
**Por que:** App inutilizavel sem output legivel e input funcional
**Verificar:** `bun run build` + testar no app real (abrir, selecionar caso, digitar)

### 2. Reescrever TerminalPane com output user-friendly
**Onde:** `legal-workbench/ccui-app/src/components/TerminalPane.tsx`
**O que:** O output do Claude Code via tmux contem escape sequences complexas (cursor movement, screen clearing). Nao basta strip de ANSI -- precisa de processamento inteligente que reconstrua o texto e idealmente renderize markdown. Referencia: `/tmp/adk-ref/src/components/ChatWorkspace.tsx` e `MarkdownRenderer.tsx`
**Por que:** Advogados nao conseguem ler output cru de terminal
**Verificar:** Abrir app, selecionar caso, ver output formatado

### 3. Corrigir input na SessionView
**Onde:** `legal-workbench/ccui-app/src/components/SessionView.tsx`
**O que:** Garantir que o input envia `{ type: "input", channel: "main", text: "texto\n" }` via WS. O `\n` e necessario para simular Enter no tmux. Verificar se WebSocketContext.sendMessage funciona corretamente.
**Por que:** Usuario nao consegue interagir com o Claude Code
**Verificar:** Abrir app, selecionar caso, digitar "1" + Enter (confirmar trust prompt)

### 4. Commitar todo o ccui-app
**Onde:** `git add legal-workbench/ccui-app/ legal-workbench/docs/plans/`
**O que:** Primeiro commit do app completo
**Por que:** Nada foi commitado ainda
**Verificar:** `git status` limpo

### 5. Definir sistema de embedding dos cases
**Onde:** Estrutura de `/home/opc/casos/<case-id>/`
**O que:** Decidir: como/quando embeddings sao gerados, pipeline (BGE-M3 via Modal? Local?), formato do knowledge.db, estrutura de pastas (base/, embeddings/, metadata/)
**Por que:** Cases precisam de knowledge base para o Claude consultar
**Verificar:** N/A (decisao de design)

### 6. CLAUDE.md pendente
**Onde:** `CLAUDE.md` (raiz) e `legal-workbench/CLAUDE.md`
**O que:** Commitar alteracoes da Phase 2 do backend
**Verificar:** `git add CLAUDE.md legal-workbench/CLAUDE.md && git commit`

## Como verificar

```bash
# Backend rodando
curl http://localhost:8005/health  # "ok"
systemctl --user status ccui-backend  # active

# Build frontend
cd legal-workbench/ccui-app && bun run build

# Testes
cd legal-workbench/ccui-app && bun run test  # 30/30

# Build Tauri completo
cd legal-workbench/ccui-app && cargo tauri build

# Transferir para PC Linux
scp legal-workbench/ccui-app/src-tauri/target/release/bundle/appimage/ccui-app_0.1.0_amd64.AppImage cmr-auto@100.102.249.9:~/Desktop/

# Caso de teste existe
curl http://localhost:8005/api/cases | python3 -m json.tool
```

## Modelo para teammates

Opus para bugs criticos de UI/UX. Sonnet para scaffold e implementacao padrao.
