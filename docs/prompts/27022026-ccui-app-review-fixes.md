# Retomada: ccui-app -- Teste Real + Continuacao do Desenvolvimento

## Contexto rapido

O ccui-app (app Tauri standalone para advogados) foi revisado por 2 agentes Opus e teve 3 correcoes P0 aplicadas: race condition WS (connect retorna Promise), seguranca shell (validators regex, TunnelState), e TerminalPane reescrito com xterm.js. MCP Bridge plugin foi adicionado (debug only). Build gerou .deb instalado no PC Linux.

O usuario vai enviar screenshots do app rodando para continuar o desenvolvimento.

## Documento de contexto

**LEIA PRIMEIRO:** `docs/contexto/27022026-ccui-app-review-fixes.md`

## Arquivos principais

- `legal-workbench/ccui-app/` -- app Tauri completo (React + Rust)
- `legal-workbench/ccui-app/src/components/TerminalPane.tsx` -- xterm.js (reescrito nesta sessao)
- `legal-workbench/ccui-app/src/contexts/WebSocketContext.tsx` -- WS com connect() Promise-based
- `legal-workbench/ccui-app/src/components/CaseSelector.tsx` -- async handleSelect
- `legal-workbench/ccui-app/src-tauri/src/lib.rs` -- Tauri commands + TunnelState + MCP bridge
- `legal-workbench/ccui-app/src-tauri/capabilities/default.json` -- permissoes restritivas
- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS (fonte de verdade)
- `legal-workbench/docs/plans/2026-02-27-ccui-app-standalone-design.md` -- design doc

## Proximos passos (por prioridade)

### 1. Avaliar screenshots do app e corrigir problemas visuais
**Onde:** componentes em `legal-workbench/ccui-app/src/components/`
**O que:** usuario vai enviar prints -- analisar e corrigir o que estiver errado
**Por que:** primeiro teste real do app
**Verificar:** `cd legal-workbench/ccui-app && bun run build`

### 2. Reescrever testes do TerminalPane
**Onde:** `legal-workbench/ccui-app/src/__tests__/TerminalPane.test.tsx`
**O que:** testes antigos testam componente removido (strip ANSI). Reescrever para xterm.js
**Por que:** testes vao falhar no proximo `bun run test`
**Verificar:** `cd legal-workbench/ccui-app && bun run test`

### 3. Corrigir Spinners (p5.js CDN)
**Onde:** `legal-workbench/ccui-app/src/components/Spinners.tsx`
**O que:** Spinners dependem de `window.p5` via CDN. Se CDN falhar, nao renderiza. Bundlar p5 ou usar CSS animations
**Por que:** fallback silencioso -- usuario nao ve spinner de loading
**Verificar:** desconectar rede e ver se spinner aparece

### 4. Definir sistema de embedding dos cases
**Onde:** estrutura de `/home/opc/casos/<case-id>/`
**O que:** pipeline de embedding (BGE-M3 via Modal?), formato do knowledge.db, acionamento
**Por que:** cases precisam de knowledge base para o Claude consultar
**Verificar:** N/A (decisao de design)

## Como verificar

```bash
# Backend rodando
curl http://localhost:8005/health  # "ok"
systemctl --user status ccui-backend  # active

# Build frontend
cd legal-workbench/ccui-app && bun run build

# Testes (VAO FALHAR -- TerminalPane.test.tsx desatualizado)
cd legal-workbench/ccui-app && bun run test

# Build Tauri completo
cd legal-workbench/ccui-app && cargo tauri build

# Transferir para PC Linux
scp legal-workbench/ccui-app/src-tauri/target/release/bundle/deb/ccui-app_0.1.0_amd64.deb cmr-auto@100.102.249.9:~/Desktop/

# Instalar no PC Linux
ssh cmr-auto@100.102.249.9 "sudo dpkg -i ~/Desktop/ccui-app_0.1.0_amd64.deb"
```

## Modelo para teammates

Opus para bugs criticos de UI/UX. Sonnet para implementacao padrao.
