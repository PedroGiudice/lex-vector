# Retomada: Build, teste do app e verificacao stj-vec

## Contexto rapido

O ccui-app recebeu varias mudancas nesta sessao: ApertureSpinner (Canvas 2D substituindo p5.js), crossfade entre telas, transicoes de sidebar, indicador de processamento no chat ("Pensando..."), e integracao frontend do reconnect_session. O backend ganhou reconnect_session e cleanup de sessoes zumbi. Docs (CLAUDE.md e ARCHITECTURE.md) foram reescritos.

Nada foi compilado nem testado no PC de destino (cmr-auto, Linux). O backend em producao ainda roda versao antiga. O stj-vec precisa de verificacao de estado.

Contexto detalhado: `docs/contexto/04032026-ccui-motion-reconnect-docs.md`

## Arquivos principais

- `legal-workbench/ccui-app/` -- app Tauri desktop (React 19 + Vite 6 + Tauri 2.3)
- `legal-workbench/ccui-backend/` -- backend Rust (axum 0.8 + tokio + tmux)
- `stj-vec/` -- busca vetorial STJ (Rust + SQLite + qdrant)

## Proximos passos (por prioridade)

### 1. Rebuildar o backend e reiniciar
**Onde:** `legal-workbench/ccui-backend/`
**O que:** Compilar release e reiniciar o servico na porta 8005
**Por que:** Backend em producao nao tem reconnect_session nem cleanup de zumbis
**Verificar:**
```bash
cd legal-workbench/ccui-backend
cargo build --release
# Parar o processo antigo e iniciar o novo
./target/release/ccui-backend
curl -s http://localhost:8005/health
curl -s http://localhost:8005/api/sessions | python3 -m json.tool
```

### 2. Build do app Tauri (.deb)
**Onde:** `legal-workbench/ccui-app/`
**O que:** Compilar frontend + Tauri bundle (.deb)
**Por que:** Mudancas de motion/spinners/reconnect nao foram testadas em build real
**Verificar:**
```bash
cd legal-workbench/ccui-app
PATH="/home/opc/.bun/bin:/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH" bun run build
CC=/usr/bin/gcc PATH="/home/opc/.bun/bin:/home/opc/.cargo/bin:/home/opc/.nvm/versions/node/v22.22.0/bin:/usr/bin:$PATH" NO_STRIP=true APPIMAGE_EXTRACT_AND_RUN=1 cargo tauri build --bundles deb
```
**ATENCAO:** Verificar que versao em Cargo.toml e tauri.conf.json estao sincronizadas antes do build.

### 3. Transferir e instalar no PC Linux
**Onde:** VM Contabo -> cmr-auto (100.102.249.9)
**O que:** SCP do .deb e dpkg -i
**Verificar:**
```bash
scp legal-workbench/ccui-app/src-tauri/target/release/bundle/deb/ccui-app_*.deb cmr-auto@100.102.249.9:/tmp/
ssh cmr-auto@100.102.249.9 "sudo dpkg -i /tmp/ccui-app_*.deb"
```

### 4. Testes no PC Linux
**Onde:** cmr-auto (app instalado)
**O que:** Testar via Tauri MCP ou manualmente:
- Criar sessao -> ver ApertureSpinner durante loading
- Chat -> ver "Pensando..." com spinner enquanto Claude processa
- Clicar em sessao na sidebar -> deve reconectar (nao destruir)
- Toggle sidebar -> deve animar slide-in/out
- Trocar entre CaseSelector e SessionView -> deve ter crossfade
**Verificar:** Sem crashes, transicoes suaves, spinner visivel

### 5. Verificar stj-vec
**Onde:** `stj-vec/`
**O que:** Verificar estado do projeto -- compila? testes passam? dados existem? server roda?
**Verificar:**
```bash
cd stj-vec
cargo build
cargo test
ls -la db/  # verificar se ha databases SQLite
# Se tiver server:
cargo run --bin stj-vec-server
curl -s http://localhost:8421/health
```

### 6. Invocar cleanup_dead_sessions no startup do backend
**Onde:** `legal-workbench/ccui-backend/src/routes.rs` ou `main.rs`
**O que:** Chamar `session_manager.cleanup_dead_sessions()` no startup do servidor para limpar sessoes zumbi acumuladas
**Por que:** O metodo existe mas nao e chamado automaticamente

## Como verificar

```bash
# Backend
cd legal-workbench/ccui-backend
cargo test -- --test-threads=1
cargo clippy -- -W clippy::pedantic

# Frontend
cd legal-workbench/ccui-app
PATH="/home/opc/.bun/bin:/home/opc/.nvm/versions/node/v22.22.0/bin:$PATH" bun run build

# stj-vec
cd stj-vec
cargo build
cargo test
```
