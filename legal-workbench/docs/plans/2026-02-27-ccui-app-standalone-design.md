# Design: ccui-app -- App Tauri Standalone para Advogados

**Data:** 2026-02-27
**Status:** Aprovado (pendente implementacao)
**Branch:** wrapper-legal-agents-front

---

## Contexto

O ccui-backend (Rust, axum+tokio+tmux) teve a Phase 2 completada: selecao de caso por ID, auto-start do Claude, auto-registro de canais de teammates, persistencia de sessoes, endpoints REST. 103 testes, clippy pedantic limpo.

O frontend ccui-v2 existe dentro do Legal Workbench (SPA React em `frontend/src/components/ccui-v2/`), mas:
- Nao usa os novos endpoints (cases, channels, case_id no protocolo)
- Design estilo IDE (sidebar com icons, window controls) inadequado para advogados
- Roda como rota `/ccui-assistant` dentro do LW -- sessoes longas competem com outros modulos

## Decisoes Tomadas

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| App separado vs rota no LW | **App Tauri standalone** | Sessoes longas precisam de janela dedicada; WS nao morre ao navegar |
| Onde o backend roda | **VM (ccui-backend na porta 8005)** | Claude Code + tmux rodam na VM, nao no PC do advogado |
| Arquitetura do app Tauri | **Client remoto** | Frontend conecta via WS/REST ao backend na VM |
| Localizacao no monorepo | **legal-workbench/ccui-app/** | Monorepo, CI compartilhado, tipos proximos |
| Direcao visual | **Evoluir ccui-v2** | Menos estetica IDE, mais chatbox profissional. Funcionalidade primeiro |

## Arquitetura

```
PC Advogado                              VM Contabo
+-------------------+    SSH tunnel      +-------------------+
| ccui-app (Tauri)  |==================>| ccui-backend      |
| React + WebView   |  ED25519 keypair  | axum + tokio      |
| tauri-plugin-shell|  -L 8005:lo:8005  | tmux sessions     |
+-------------------+                   | Claude Code CLI   |
        |                               +-------------------+
        v
  WS localhost:8005
  (dentro do tunnel)
```

### Camada de transporte: SSH tunnel automatico

O app Tauri abre um tunnel SSH automaticamente ao iniciar:
- **Primeira execucao:** gera par de chaves ED25519, exibe pub key para registrar na VM
- **Execucoes seguintes:** abre `ssh -N -L 8005:localhost:8005 opc@<vm-host> -i ~/.ccui/id_ed25519`
- **Frontend React** conecta WS a `localhost:8005` (transparente, sem saber do SSH)
- **Beneficios:** porta 8005 nunca exposta; criptografia + auth por chave; reconexao robusta
- **Backend nao muda:** continua servindo em localhost:8005

### Tauri commands para SSH

```rust
#[tauri::command]
async fn generate_keypair() -> Result<String, String> {
    // Gera ~/.ccui/id_ed25519 + id_ed25519.pub
    // Retorna conteudo da pub key para o usuario registrar na VM
}

#[tauri::command]
async fn open_tunnel(host: String) -> Result<(), String> {
    // Executa ssh -N -L 8005:localhost:8005 opc@host -i key
    // via tauri-plugin-shell como processo filho gerenciado
}

#[tauri::command]
async fn check_tunnel() -> Result<bool, String> {
    // Verifica se o processo SSH esta vivo e localhost:8005 responde
}
```

O app Tauri e um thin client com tunnel SSH. Toda logica de sessao, tmux, e Claude fica no backend.

## Estrutura do Projeto

```
legal-workbench/ccui-app/
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json        # CSP permite WS para host configuravel
│   ├── src/
│   │   ├── main.rs
│   │   └── lib.rs             # Commands: get_config, check_health
│   └── icons/
├── src/
│   ├── main.tsx
│   ├── App.tsx                # Router: CaseSelector -> SessionView
│   ├── components/
│   │   ├── CaseSelector.tsx   # GET /api/cases, lista casos, inicia sessao
│   │   ├── SessionView.tsx    # View principal (header + channel tabs + terminal)
│   │   ├── ChannelTabs.tsx    # Abas: "main" + teammates dinamicos
│   │   ├── TerminalPane.tsx   # Output streaming de um canal
│   │   ├── ConnectionStatus.tsx
│   │   └── ui/
│   ├── contexts/
│   │   ├── SessionContext.tsx  # case_id, session_id, channels[]
│   │   └── WebSocketContext.tsx
│   ├── hooks/
│   │   └── useCcuiApi.ts      # fetch wrappers para endpoints REST
│   └── types/
│       └── protocol.ts        # ClientMessage, ServerMessage (match backend)
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── index.html
```

## Fluxo do Usuario

```
1. Advogado abre ccui-app
2. App verifica conexao com backend (health check)
3. CaseSelector: lista casos via GET /api/cases
   - Mostra: nome do caso, status (ready/nao-ready), qtd documentos
   - Advogado clica num caso
4. App envia CreateSession{case_id} via WS
5. Backend cria sessao tmux, auto-start Claude, registra canal "main"
6. SessionView: terminal mostra output do Claude (canal "main")
7. Se Claude spawna teammates: AgentJoined chega via WS
   - ChannelTabs adiciona aba para cada teammate
   - Advogado pode alternar entre abas
8. Reconexao: GET /api/sessions/{id}/channels lista canais ativos
```

## Protocolo WS (backend ja implementado)

### Client -> Server
```typescript
type ClientMessage =
  | { type: "create_session"; case_id: string }
  | { type: "input"; session_id: string; data: string; channel?: string }
  | { type: "resize"; session_id: string; cols: number; rows: number }
  | { type: "destroy_session"; session_id: string }
```

### Server -> Client
```typescript
type ServerMessage =
  | { type: "session_created"; session_id: string; case_id?: string }
  | { type: "output"; session_id: string; data: string; channel?: string }
  | { type: "session_destroyed"; session_id: string }
  | { type: "agent_joined"; name: string; tmux_session: string; pane_id: string }
  | { type: "agent_left"; name: string }
  | { type: "error"; message: string }
```

## Endpoints REST (backend ja implementado)

| Metodo | Path | Resposta |
|--------|------|----------|
| GET | /health | "ok" |
| GET | /api/cases | `{ cases: [{ id, path, ready, doc_count, last_modified }] }` |
| GET | /api/sessions | `{ sessions: [...] }` |
| GET | /api/sessions/{id}/channels | `{ channels: [{ name, pane_id }] }` |

## Interacao do Advogado

O advogado e um **usuario ativo**, nao um observador passivo:

1. Seleciona o caso no CaseSelector
2. Digita instrucoes para o Claude (campo de input na SessionView)
3. Acompanha o output em tempo real (streaming WS)
4. Pode alternar entre canais de teammates
5. Pode enviar input para canais especificos (channel no ClientMessage)

O campo de input envia `{ type: "input", session_id, data, channel }` via WS.

## Autenticacao

**Nao ha autenticacao no ccui-backend.** O SSH tunnel e a autenticacao:
- Apenas quem tem a chave privada ED25519 consegue abrir o tunnel
- O backend escuta apenas em localhost -- inacessivel sem tunnel
- Multi-usuario: cada advogado tem seu par de chaves, todos acessam o mesmo backend

## Tauri Commands (completo)

```rust
// Configuracao
#[tauri::command]
fn get_config() -> AppConfig {
    AppConfig { vm_host: "100.123.73.128".into(), local_port: 8005 }
}

// SSH keypair
#[tauri::command]
async fn generate_keypair() -> Result<String, String> { /* pub key */ }

// Tunnel
#[tauri::command]
async fn open_tunnel(host: String) -> Result<(), String> { /* ssh -N -L */ }

#[tauri::command]
async fn check_tunnel() -> Result<bool, String> { /* tunnel alive? */ }

// Health
#[tauri::command]
async fn check_health() -> Result<bool, String> {
    // GET localhost:8005/health (via tunnel)
}
```

## Componentes a Reutilizar do ccui-v2

| Componente | Acao |
|-----------|------|
| WebSocketContext | Copiar e adaptar (remover auth cookie, adicionar case_id) |
| ConnectionStatus | Copiar como esta |
| ErrorBanner | Copiar como esta |
| Spinners | Copiar como esta |
| CCuiChatInterface | Base para TerminalPane (simplificar, remover tool calls UI) |
| CCuiLayout | NAO copiar (redesign completo) |
| CCuiFileTree | NAO copiar (irrelevante para advogados) |

## Direcao Visual

- Remover estetica IDE (window controls fake, icon rail, file tree)
- Fundo escuro mantido (profissional)
- Seletor de caso: cards ou lista limpa com status claro
- Sessao: header com info do caso, abas de canal, area de output
- Menos chrome, mais conteudo
- Cor de destaque #d97757 mantida (identidade visual)

## Plano de Implementacao (para agent team)

### Task 1: Scaffold Tauri app
- `bun create tauri-app` em `legal-workbench/ccui-app/`
- Configurar Vite, Tailwind, TypeScript
- CSP no tauri.conf.json para permitir WS a localhost:8005
- Tauri commands: get_config, check_health, generate_keypair, open_tunnel, check_tunnel
- Deps Rust: tauri, tauri-plugin-shell, tauri-plugin-store, serde, tokio

### Task 2: Tipos e contextos
- `types/protocol.ts` com ClientMessage, ServerMessage
- WebSocketContext adaptado (conexao sob demanda, nao no mount)
- SessionContext (case_id, session_id, channels state)
- `useCcuiApi` hook para endpoints REST

### Task 3: CaseSelector
- Componente que chama GET /api/cases
- Lista de casos com nome, ready badge, doc_count
- Click inicia sessao (envia CreateSession via WS)
- Estados: loading, empty, error

### Task 4: SessionView + ChannelTabs + TerminalPane
- SessionView: layout principal apos selecionar caso
- ChannelTabs: "main" fixo + tabs dinamicas por AgentJoined/AgentLeft
- TerminalPane: streaming do output WS, auto-scroll
- Reconexao via GET /api/sessions/{id}/channels

### Task 5: Testes
- Unit tests para hooks e contextos (vitest)
- Testes de integracao para protocolo WS (mock server)

### Task 6: Polish visual
- Evoluir visual: remover chrome IDE, ajustar para chatbox profissional
- Responsividade basica da janela Tauri

## Pontas Soltas (resolver durante implementacao)

| Ponta | Decisao necessaria | Quando |
|-------|-------------------|--------|
| Setup flow (primeira execucao) | Tela de onboarding: gerar chave, configurar host VM, testar conexao | Task 1 |
| Persistencia de config | tauri-plugin-store para salvar vm_host, keypair path | Task 1 |
| Input field design | Textarea simples vs terminal-like input | Task 4 |
| Notificacoes desktop | Notificar quando agente termina trabalho (tauri-plugin-notification) | Task 6 |
| Build para Windows/Linux/Mac | CI/CD para multiplas plataformas | Pos-MVP |
| Rota /ccui-assistant no LW | Remover apos ccui-app funcionar | Pos-MVP |

## Verificacao de Completude

- [x] Backend endpoints ja existem e estao testados (103 testes)
- [x] Protocolo WS documentado e match com backend
- [x] Componentes reutilizaveis identificados
- [x] Fluxo do usuario definido
- [x] Tauri commands especificados (config + SSH + health)
- [x] Tasks decompostas para agent team
- [x] Camada de transporte definida (SSH tunnel automatico)
- [x] Autenticacao definida (ED25519 keypair, sem auth no backend)
- [x] Modelo de interacao definido (advogado ativo: input + output)
