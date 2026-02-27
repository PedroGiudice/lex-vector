# Retomada: ccui-app -- Implementacao com Agent Team

## Contexto rapido

Design do ccui-app (app Tauri standalone para advogados) esta completo e aprovado. Nenhum codigo escrito ainda. O app sera um client remoto que conecta via WS ao ccui-backend na VM.

## Documento de design

**LEIA PRIMEIRO:** `legal-workbench/docs/plans/2026-02-27-ccui-app-standalone-design.md`

Contem: estrutura do projeto, fluxo do usuario, protocolo WS, endpoints REST, componentes reutilizaveis, 6 tasks decompostas.

## Arquitetura em uma frase

App Tauri no PC do advogado (React + WebView) conecta via WS/REST ao ccui-backend (Rust, porta 8005) rodando na VM Contabo. Backend nao muda.

## Backend de referencia (ja funcional, 103 testes)

- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS (ClientMessage, ServerMessage)
- `legal-workbench/ccui-backend/src/routes.rs` -- handlers REST (cases, sessions, channels)
- `legal-workbench/ccui-backend/src/config.rs` -- AppConfig com cases_dir

## Frontend existente (referencia, nao copiar cegamente)

- `legal-workbench/frontend/src/components/ccui-v2/` -- componentes do chat atual
- `legal-workbench/frontend/src/components/ccui-v2/contexts/WebSocketContext.tsx` -- WS com reconnect
- `legal-workbench/frontend/src/components/ccui-v2/CCuiChatInterface.tsx` -- chat completo (~700 linhas)

## O que fazer

1. Invocar `superpowers:writing-plans` para plano de implementacao detalhado
2. Invocar `agent-teams` para lancar o team
3. Tasks do design (6 no total -- ver design doc):
   - Task 1: Scaffold Tauri app (`bun create tauri-app`)
   - Task 2: Tipos, contextos, hooks
   - Task 3: CaseSelector
   - Task 4: SessionView + ChannelTabs + TerminalPane
   - Task 5: Testes
   - Task 6: Polish visual

## Decisoes ja tomadas (nao renegociar)

- App Tauri standalone (nao rota no LW)
- Monorepo em `legal-workbench/ccui-app/`
- Client remoto (backend na VM, nao embutido)
- **Transporte: SSH tunnel automatico** com par de chaves ED25519
  - App gera keypair na primeira execucao
  - Abre `ssh -N -L 8005:localhost:8005` automaticamente
  - Frontend conecta WS a localhost:8005 (transparente)
  - Backend nao precisa de auth/TLS -- SSH faz tudo
- **Advogado e usuario ativo:** digita prompts, acompanha output, alterna canais
- Funcionalidade primeiro, visual depois
- Menos estetica IDE, mais chatbox profissional

## Modelo para teammates

Perguntar ao usuario. Sugestao: sonnet para frontend (custo-beneficio).

## Pendencia pre-existente

Commitar CLAUDE.md (raiz + LW) com mudancas da Phase 2:
```bash
cd /home/opc/lex-vector
git add CLAUDE.md legal-workbench/CLAUDE.md
git commit -m "docs: atualizar CLAUDE.md com arquitetura ccui-backend phase 2"
```
