# Retomada: ccui-backend -- Proximas Fases apos Phase 2

## Contexto rapido

O ccui-backend (Rust, axum+tokio+tmux) teve a Phase 2 completada e mergeada na main. O backend agora suporta: selecao de caso por ID, auto-start do Claude, auto-registro de canais de teammates, persistencia de sessoes, e endpoints REST para listar casos e canais. Sao 103 testes passando, clippy pedantic limpo.

O backend esta funcional mas precisa de: integracao Docker, frontend wrapper, e testes E2E. Nenhuma dessas tarefas e Rust -- sao frontend (React), DevOps (Docker), e possivelmente Python (testes E2E).

## Arquivos principais

- `legal-workbench/ccui-backend/src/routes.rs` -- router principal, handlers HTTP e WS
- `legal-workbench/ccui-backend/src/session.rs` -- SessionManager, persistencia
- `legal-workbench/ccui-backend/src/pane_proxy.rs` -- canais, register/unregister
- `legal-workbench/ccui-backend/src/ws.rs` -- protocolo WS (ClientMessage, ServerMessage)
- `docs/contexto/27022026-ccui-backend-phase2.md` -- contexto detalhado desta sessao
- `legal-workbench/docs/plans/2026-02-27-ccui-backend-phase2-design.md` -- design doc original

## Pendencia imediata

Commitar alteracoes nos CLAUDE.md (raiz + legal-workbench) que ficaram pendentes:
```bash
cd /home/opc/lex-vector
git add CLAUDE.md legal-workbench/CLAUDE.md
git commit -m "docs: atualizar CLAUDE.md com arquitetura ccui-backend phase 2"
```

## Proximos passos (por prioridade)

### 1. Integrar ccui-backend no Docker Compose
**Onde:** `legal-workbench/docker/docker-compose.yml`
**O que:** Adicionar servico `ccui-backend` com build do Dockerfile existente, porta 8005, rota Traefik `/api/ccui`
**Por que:** O backend precisa rodar junto com os outros servicos
**Verificar:** `docker compose up -d && curl localhost:8005/health`
**Agente:** `cicd-operator` ou `backend-developer`

### 2. Frontend wrapper -- selecao de caso
**Onde:** `legal-workbench/frontend/src/pages/` (novo componente)
**O que:** Pagina que chama `GET /api/cases`, mostra lista de casos com status (ready/nao-ready, doc_count), permite selecionar e iniciar sessao
**Por que:** Advogado precisa de interface visual para escolher o caso
**Verificar:** `bun run dev` + navegar para a pagina
**Agente:** `frontend-developer`

### 3. Frontend wrapper -- visualizacao de sessao
**Onde:** `legal-workbench/frontend/src/pages/` (novo componente)
**O que:** Terminal web conectado via WebSocket ao ccui-backend, mostrando output do Claude. Suporte a multiplos canais (abas para cada agente/teammate)
**Por que:** Core da experiencia do advogado -- ver o Claude trabalhando
**Verificar:** Criar sessao via UI, verificar output aparece
**Agente:** `frontend-developer`

### 4. Teste flaky team_watcher
**Onde:** `legal-workbench/ccui-backend/tests/team_watcher_integration.rs`
**O que:** `agent_left_emitted_when_member_removed` falha com timeout intermitentemente
**Por que:** Instabilidade afeta CI
**Verificar:** `cargo test --test team_watcher_integration -- --test-threads=1` rodando 10x sem falha
**Agente:** `rust-developer` ou `test-writer-fixer`

### 5. Testes E2E do fluxo completo
**Onde:** Novo arquivo de teste ou script
**O que:** Fluxo: criar sessao com case_id -> verificar Claude iniciou -> simular agent_joined -> verificar canal registrado -> reconectar e listar canais
**Por que:** Validar integracao real entre todos os componentes
**Agente:** `test-writer-fixer`

## Como verificar estado atual

```bash
cd /home/opc/lex-vector/legal-workbench/ccui-backend
cargo test -- --test-threads=1        # 103 testes
cargo clippy -- -W clippy::pedantic   # zero warnings
cargo run                             # porta 8005
curl localhost:8005/health            # "ok"
curl localhost:8005/api/cases         # lista casos
```
