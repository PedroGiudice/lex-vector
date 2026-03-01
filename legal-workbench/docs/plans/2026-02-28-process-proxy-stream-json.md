# ProcessProxy + stream-json: Plano de Implementacao Backend

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Substituir o PaneProxy (tmux pipe-pane + bytes brutos) por ProcessProxy que spawna `claude -p --output-format stream-json` como child process, deserializa NDJSON tipado e emite ChatUpdate via WebSocket.

**Architecture:** O backend deixa de usar tmux para captura de output. Em vez disso, spawna Claude Code como child process headless via `tokio::process::Command` com flags `--output-format stream-json --input-format stream-json --include-partial-messages --permission-mode bypassPermissions`. Stdout emite NDJSON (uma linha JSON por evento). O backend deserializa cada linha em tipos Rust e retransmite como ChatUpdate tipado via WebSocket. tmux permanece apenas para developer mode (terminal bruto).

**Tech Stack:** Rust, tokio (async runtime), serde/serde_json (deserializacao NDJSON), axum (HTTP/WS), tokio::process (child process management)

---

## Resumo Executivo

O ccui-backend atual usa tmux pipe-pane para capturar output do Claude Code. Isso produz output TUI bruto (ANSI escapes, cursor movement, spinners) impossivel de parsear. A solucao e spawnar Claude Code em modo headless (`claude -p --output-format stream-json`) como child process, recebendo NDJSON tipado no stdout. Isso elimina 100% da heuristica de parsing e permite um protocolo WS tipado com mensagens semanticas (texto, tool_use, thinking, resultado).

---

## Task 1: Tipos Rust para o schema NDJSON do Claude Code

**Files:**
- Create: `src/claude_types.rs`
- Modify: `src/lib.rs` (adicionar `pub mod claude_types;`)

O schema NDJSON do Claude Code (via Agent SDK) emite estas mensagens:

### Step 1: Criar modulo de tipos

```rust
//! Tipos para deserializacao do output NDJSON do Claude Code (`--output-format stream-json`).
//!
//! Referencia: https://platform.claude.com/docs/en/agent-sdk/typescript
//! O stream emite uma linha JSON por evento. Cada linha e um `SDKMessage`.

use serde::Deserialize;

// ---------------------------------------------------------------------------
// SDKMessage -- union discriminada por `type`
// ---------------------------------------------------------------------------

/// Mensagem emitida pelo Claude Code em modo stream-json.
/// Apenas os tipos relevantes para o frontend sao modelados;
/// variantes desconhecidas sao capturadas por `Unknown`.
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "type")]
pub enum SDKMessage {
    /// Inicializacao da sessao.
    #[serde(rename = "system")]
    System(SystemMessage),

    /// Resposta completa do assistente (um turno inteiro).
    #[serde(rename = "assistant")]
    Assistant(AssistantMessage),

    /// Mensagem do usuario (replay ou sintetica).
    #[serde(rename = "user")]
    User(UserMessage),

    /// Resultado final da query.
    #[serde(rename = "result")]
    Result(ResultMessage),

    /// Evento de streaming parcial (requer --include-partial-messages).
    #[serde(rename = "stream_event")]
    StreamEvent(StreamEventMessage),
}

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct SystemMessage {
    pub subtype: String,
    pub session_id: String,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub tools: Option<Vec<String>>,
    #[serde(default)]
    pub claude_code_version: Option<String>,
    #[serde(default)]
    pub cwd: Option<String>,
}

// ---------------------------------------------------------------------------
// Assistant
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct AssistantMessage {
    pub uuid: String,
    pub session_id: String,
    pub message: AnthropicMessage,
    #[serde(default)]
    pub parent_tool_use_id: Option<String>,
}

/// Subconjunto do `BetaMessage` da Anthropic API.
#[derive(Debug, Clone, Deserialize)]
pub struct AnthropicMessage {
    pub id: String,
    pub content: Vec<ContentBlock>,
    pub model: String,
    #[serde(default)]
    pub stop_reason: Option<String>,
    #[serde(default)]
    pub usage: Option<Usage>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Usage {
    #[serde(default)]
    pub input_tokens: u64,
    #[serde(default)]
    pub output_tokens: u64,
    #[serde(default)]
    pub cache_read_input_tokens: Option<u64>,
    #[serde(default)]
    pub cache_creation_input_tokens: Option<u64>,
}

// ---------------------------------------------------------------------------
// Content blocks
// ---------------------------------------------------------------------------

/// Bloco de conteudo dentro de uma mensagem do assistente.
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "type")]
pub enum ContentBlock {
    #[serde(rename = "text")]
    Text { text: String },

    #[serde(rename = "thinking")]
    Thinking {
        thinking: String,
        #[serde(default)]
        signature: Option<String>,
    },

    #[serde(rename = "tool_use")]
    ToolUse {
        id: String,
        name: String,
        input: serde_json::Value,
    },

    #[serde(rename = "tool_result")]
    ToolResult {
        tool_use_id: String,
        content: serde_json::Value,
        #[serde(default)]
        is_error: Option<bool>,
    },
}

// ---------------------------------------------------------------------------
// User
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct UserMessage {
    pub session_id: String,
    #[serde(default)]
    pub uuid: Option<String>,
    #[serde(default)]
    pub parent_tool_use_id: Option<String>,
}

// ---------------------------------------------------------------------------
// Result
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct ResultMessage {
    pub session_id: String,
    pub subtype: String,
    #[serde(default)]
    pub duration_ms: Option<u64>,
    #[serde(default)]
    pub is_error: Option<bool>,
    #[serde(default)]
    pub num_turns: Option<u64>,
    #[serde(default)]
    pub result: Option<String>,
    #[serde(default)]
    pub total_cost_usd: Option<f64>,
}

// ---------------------------------------------------------------------------
// StreamEvent (partial messages)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct StreamEventMessage {
    pub session_id: String,
    pub uuid: String,
    #[serde(default)]
    pub parent_tool_use_id: Option<String>,
    /// O evento raw da Anthropic Streaming API.
    /// Deserializado como Value generico porque o schema e extenso
    /// e varia entre versoes. O backend extrai apenas o necessario.
    pub event: serde_json::Value,
}
```

### Step 2: Registrar modulo em lib.rs

Adicionar `pub mod claude_types;` em `src/lib.rs`.

### Step 3: Commit

```bash
git add src/claude_types.rs src/lib.rs
git commit -m "feat(ccui-backend): tipos Rust para schema NDJSON stream-json do Claude Code"
```

---

## Task 2: ChatUpdate -- protocolo WS envelope (server -> client)

**Files:**
- Modify: `src/ws.rs` (adicionar variantes ChatUpdate ao ServerMessage)
- Create: `src/message_part.rs` (tipo MessagePart compartilhado backend<->frontend)

### Decisao de alinhamento (2026-02-28)

O frontend espera 3 tipos simples: `chat_start`, `chat_delta`, `chat_end`. O backend agrupa os SDKMessage events nesse envelope, emitindo `MessagePart` serializado dentro de cada delta. Isso permite ao frontend acumular parts por message_id sem conhecer os tipos internos do backend.

### Step 1: Criar MessagePart (tipo compartilhado)

```rust
// src/message_part.rs
use serde::Serialize;

/// Parte de uma mensagem do assistente, emitida via WS como chat_delta.
/// Alinhado 1:1 com o tipo TypeScript MessagePart do frontend.
#[derive(Debug, Clone, Serialize)]
pub struct MessagePart {
    #[serde(rename = "type")]
    pub kind: MessagePartType,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<MessagePartMetadata>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MessagePartType {
    Text,
    Thinking,
    ToolUse,
    ToolResult,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct MessagePartMetadata {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_error: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_streaming: Option<bool>,
}
```

### Step 2: Estender ServerMessage com envelope chat_start/delta/end

Adicionar ao enum `ServerMessage` em `ws.rs`:

```rust
/// Inicio de uma nova mensagem do assistente.
#[serde(rename = "chat_start")]
ChatStart {
    message_id: String,
    session_id: String,
},

/// Parte incremental de uma mensagem (texto, thinking, tool_use, tool_result).
#[serde(rename = "chat_delta")]
ChatDelta {
    message_id: String,
    session_id: String,
    part: MessagePart,
},

/// Fim de uma mensagem do assistente.
#[serde(rename = "chat_end")]
ChatEnd {
    message_id: String,
    session_id: String,
},

/// Sessao Claude inicializada (metadata, nao faz parte do fluxo de chat).
#[serde(rename = "chat_init")]
ChatInit {
    session_id: String,
    model: String,
    claude_session_id: String,
},
```

### Step 3: Estender ClientMessage para envio via stream-json input

Adicionar ao enum `ClientMessage`:

```rust
/// Envia prompt para o Claude via stream-json input.
#[serde(rename = "chat_input")]
ChatInput {
    session_id: String,
    text: String,
},
```

### Step 4: Registrar modulos em lib.rs

Adicionar `pub mod message_part;` em `src/lib.rs`.

### Step 5: Commit

```bash
git add src/message_part.rs src/ws.rs src/lib.rs
git commit -m "feat(ccui-backend): protocolo WS envelope chat_start/delta/end + MessagePart"
```

---

## Task 3: ProcessProxy -- core

**Files:**
- Create: `src/process_proxy.rs`
- Modify: `src/lib.rs` (adicionar `pub mod process_proxy;`)

### Step 1: Implementar ProcessProxy

```rust
//! [`ProcessProxy`] -- bridge entre child process Claude Code (stream-json) e broadcast WS.
//!
//! Substitui o PaneProxy. Spawna `claude -p --output-format stream-json` como child process,
//! le stdout linha por linha (NDJSON), deserializa em SDKMessage e emite ChatUpdate no broadcast.

use std::collections::HashMap;
use std::sync::Arc;

use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, Command};
use tokio::sync::{broadcast, RwLock};
use tokio_util::sync::CancellationToken;

use crate::claude_types::{ContentBlock, SDKMessage};
use crate::config::AppConfig;
use crate::error::AppError;
use crate::ws::ServerMessage;

/// Estado de um child process Claude Code.
struct ProcessState {
    child: Child,
    cancel: CancellationToken,
    claude_session_id: Option<String>,
}

/// Bridge: child process Claude Code (NDJSON) <-> broadcast WebSocket.
#[derive(Clone)]
pub struct ProcessProxy {
    config: AppConfig,
    processes: Arc<RwLock<HashMap<String, ProcessState>>>,
    tx: broadcast::Sender<ServerMessage>,
}

impl ProcessProxy {
    #[must_use]
    pub fn new(config: AppConfig, tx: broadcast::Sender<ServerMessage>) -> Self {
        Self {
            config,
            processes: Arc::new(RwLock::new(HashMap::new())),
            tx,
        }
    }

    /// Spawna um processo Claude Code headless para a sessao dada.
    ///
    /// O processo roda `claude -p --output-format stream-json --input-format stream-json
    /// --include-partial-messages --permission-mode bypassPermissions`.
    ///
    /// Prompt inicial e enviado via stdin como primeira mensagem stream-json.
    pub async fn spawn_process(
        &self,
        session_id: &str,
        working_dir: Option<&str>,
        initial_prompt: Option<&str>,
    ) -> Result<(), AppError> {
        let mut cmd = Command::new(&self.config.claude_bin);
        cmd.arg("-p")
            .arg("--output-format").arg("stream-json")
            .arg("--input-format").arg("stream-json")
            .arg("--include-partial-messages")
            .arg("--permission-mode").arg("bypassPermissions");

        // Flags adicionais do config (ex: --dangerously-skip-permissions)
        for flag in &self.config.claude_flags {
            cmd.arg(flag);
        }

        if let Some(dir) = working_dir {
            cmd.current_dir(dir);
        }

        // Desabilitar deteccao de sessao aninhada
        cmd.env("CLAUDECODE", "");

        cmd.stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());

        // Se tiver prompt inicial simples, passar como argumento
        if let Some(prompt) = initial_prompt {
            cmd.arg(prompt);
        }

        let mut child = cmd.spawn().map_err(|e| {
            AppError::Process(format!("falha ao spawnar claude: {e}"))
        })?;

        let stdout = child.stdout.take().ok_or_else(|| {
            AppError::Process("stdout nao capturado".into())
        })?;

        let stderr = child.stderr.take().ok_or_else(|| {
            AppError::Process("stderr nao capturado".into())
        })?;

        let cancel = CancellationToken::new();

        let state = ProcessState {
            child,
            cancel: cancel.clone(),
            claude_session_id: None,
        };

        self.processes
            .write()
            .await
            .insert(session_id.to_owned(), state);

        // Task: le stdout NDJSON e emite no broadcast
        let tx = self.tx.clone();
        let sid = session_id.to_owned();
        let cancel_clone = cancel.clone();
        let processes = self.processes.clone();
        tokio::spawn(async move {
            let reader = BufReader::new(stdout);
            let mut lines = reader.lines();

            loop {
                tokio::select! {
                    line = lines.next_line() => {
                        match line {
                            Ok(Some(line)) if !line.trim().is_empty() => {
                                match serde_json::from_str::<SDKMessage>(&line) {
                                    Ok(msg) => {
                                        emit_chat_update(&tx, &sid, &msg, &processes).await;
                                    }
                                    Err(e) => {
                                        tracing::debug!(
                                            session_id = %sid,
                                            line = %line.chars().take(200).collect::<String>(),
                                            "NDJSON parse error: {e}"
                                        );
                                    }
                                }
                            }
                            Ok(Some(_)) => {} // linha vazia
                            Ok(None) => {
                                tracing::info!(session_id = %sid, "claude stdout EOF");
                                break;
                            }
                            Err(e) => {
                                tracing::warn!(session_id = %sid, "erro lendo stdout: {e}");
                                break;
                            }
                        }
                    }
                    () = cancel_clone.cancelled() => {
                        tracing::debug!(session_id = %sid, "stdout reader cancelado");
                        break;
                    }
                }
            }

            // Notificar que a sessao encerrou via chat_end sintetico
            let _ = tx.send(ServerMessage::ChatEnd {
                message_id: format!("exit_{sid}"),
                session_id: sid.clone(),
            });
        });

        // Task: drena stderr para logs
        let sid_err = session_id.to_owned();
        tokio::spawn(async move {
            let reader = BufReader::new(stderr);
            let mut lines = reader.lines();
            while let Ok(Some(line)) = lines.next_line().await {
                if !line.trim().is_empty() {
                    tracing::debug!(session_id = %sid_err, stderr = %line);
                }
            }
        });

        Ok(())
    }

    /// Envia input para o processo Claude via stdin (stream-json format).
    pub async fn send_input(&self, session_id: &str, text: &str) -> Result<(), AppError> {
        let mut guard = self.processes.write().await;
        let state = guard.get_mut(session_id).ok_or_else(|| {
            AppError::Process(format!("processo nao encontrado: {session_id}"))
        })?;

        let stdin = state.child.stdin.as_mut().ok_or_else(|| {
            AppError::Process("stdin nao disponivel".into())
        })?;

        // Formato stream-json input: {"type":"user","content":[{"type":"text","text":"..."}]}
        let msg = serde_json::json!({
            "type": "user",
            "content": [{"type": "text", "text": text}]
        });
        let mut line = serde_json::to_string(&msg).map_err(|e| {
            AppError::Process(format!("json serialize: {e}"))
        })?;
        line.push('\n');

        stdin.write_all(line.as_bytes()).await.map_err(|e| {
            AppError::Process(format!("stdin write: {e}"))
        })?;
        stdin.flush().await.map_err(|e| {
            AppError::Process(format!("stdin flush: {e}"))
        })?;

        Ok(())
    }

    /// Encerra o processo Claude de uma sessao (graceful: SIGTERM, depois SIGKILL).
    pub async fn kill_process(&self, session_id: &str) -> Result<(), AppError> {
        let mut guard = self.processes.write().await;
        if let Some(mut state) = guard.remove(session_id) {
            state.cancel.cancel();
            // Tenta kill graceful
            let _ = state.child.kill().await;
        }
        Ok(())
    }

    /// Lista sessoes com processos ativos.
    pub async fn list_sessions(&self) -> Vec<String> {
        self.processes.read().await.keys().cloned().collect()
    }
}

/// Converte SDKMessage em envelope chat_start/chat_delta/chat_end e emite no broadcast.
/// Protocolo alinhado com frontend: 3 tipos simples com MessagePart dentro de chat_delta.
async fn emit_chat_update(
    tx: &broadcast::Sender<ServerMessage>,
    session_id: &str,
    msg: &SDKMessage,
    processes: &Arc<RwLock<HashMap<String, ProcessState>>>,
) {
    use crate::message_part::{MessagePart, MessagePartType, MessagePartMetadata};

    match msg {
        SDKMessage::System(sys) => {
            if let Some(state) = processes.write().await.get_mut(session_id) {
                state.claude_session_id = Some(sys.session_id.clone());
            }
            let _ = tx.send(ServerMessage::ChatInit {
                session_id: session_id.to_owned(),
                model: sys.model.clone().unwrap_or_default(),
                claude_session_id: sys.session_id.clone(),
            });
        }

        SDKMessage::Assistant(asst) => {
            let message_id = asst.uuid.clone();
            let _ = tx.send(ServerMessage::ChatStart {
                message_id: message_id.clone(),
                session_id: session_id.to_owned(),
            });

            for block in &asst.message.content {
                let part = match block {
                    ContentBlock::Text { text } => MessagePart {
                        kind: MessagePartType::Text,
                        content: text.clone(),
                        metadata: None,
                    },
                    ContentBlock::Thinking { thinking, .. } => MessagePart {
                        kind: MessagePartType::Thinking,
                        content: thinking.clone(),
                        metadata: None,
                    },
                    ContentBlock::ToolUse { id, name, input } => MessagePart {
                        kind: MessagePartType::ToolUse,
                        content: serde_json::to_string(input).unwrap_or_default(),
                        metadata: Some(MessagePartMetadata {
                            tool_name: Some(name.clone()),
                            tool_id: Some(id.clone()),
                            is_error: None,
                            is_streaming: None,
                        }),
                    },
                    ContentBlock::ToolResult { tool_use_id, content, is_error } => MessagePart {
                        kind: MessagePartType::ToolResult,
                        content: serde_json::to_string(content).unwrap_or_default(),
                        metadata: Some(MessagePartMetadata {
                            tool_name: None,
                            tool_id: Some(tool_use_id.clone()),
                            is_error: *is_error,
                            is_streaming: None,
                        }),
                    },
                };
                let _ = tx.send(ServerMessage::ChatDelta {
                    message_id: message_id.clone(),
                    session_id: session_id.to_owned(),
                    part,
                });
            }

            let _ = tx.send(ServerMessage::ChatEnd {
                message_id,
                session_id: session_id.to_owned(),
            });
        }

        SDKMessage::Result(_res) => {
            // Result emitido como chat_end do ultimo turno (ja emitido acima).
            // Metadata de custo/duracao pode ser adicionada ao ChatEnd futuramente.
        }

        SDKMessage::StreamEvent(evt) => {
            let message_id = evt.uuid.clone();
            if let Some(event_type) = evt.event.get("type").and_then(|v| v.as_str()) {
                if event_type == "content_block_delta" {
                    if let Some(delta) = evt.event.get("delta") {
                        let delta_type = delta.get("type").and_then(|v| v.as_str());
                        let part = match delta_type {
                            Some("text_delta") => delta.get("text").and_then(|v| v.as_str()).map(|t| {
                                MessagePart {
                                    kind: MessagePartType::Text,
                                    content: t.to_owned(),
                                    metadata: Some(MessagePartMetadata {
                                        tool_name: None, tool_id: None,
                                        is_error: None, is_streaming: Some(true),
                                    }),
                                }
                            }),
                            Some("thinking_delta") => delta.get("thinking").and_then(|v| v.as_str()).map(|t| {
                                MessagePart {
                                    kind: MessagePartType::Thinking,
                                    content: t.to_owned(),
                                    metadata: Some(MessagePartMetadata {
                                        tool_name: None, tool_id: None,
                                        is_error: None, is_streaming: Some(true),
                                    }),
                                }
                            }),
                            _ => None,
                        };
                        if let Some(part) = part {
                            let _ = tx.send(ServerMessage::ChatDelta {
                                message_id,
                                session_id: session_id.to_owned(),
                                part,
                            });
                        }
                    }
                }
            }
        }

        SDKMessage::User(_) => {}
    }
}
```

### Step 2: Adicionar variante `Process` ao error.rs

Adicionar ao enum `AppError`:

```rust
#[error("process error: {0}")]
Process(String),
```

### Step 3: Registrar modulo em lib.rs

Adicionar `pub mod process_proxy;` em `src/lib.rs`.

### Step 4: Commit

```bash
git add src/process_proxy.rs src/error.rs src/lib.rs
git commit -m "feat(ccui-backend): ProcessProxy -- spawna Claude headless via stream-json"
```

---

## Task 4: Atualizar config.rs

**Files:**
- Modify: `src/config.rs`

### Step 1: Remover campos exclusivos do tmux pipe-pane, adicionar campos do ProcessProxy

Campos a remover: `pane_log_dir`, `capture_poll_ms`, `pane_health_interval_secs`.
Manter: `tmux_session_prefix` (para developer mode futuro).

Adicionar:

```rust
/// Timeout em segundos para o processo Claude responder apos spawn.
pub process_start_timeout_secs: u64,
```

Default: `30`.

### Step 2: Commit

```bash
git add src/config.rs
git commit -m "refactor(ccui-backend): config.rs -- campos ProcessProxy, remover pane_log_dir"
```

---

## Task 5: Atualizar AppState e routes.rs

**Files:**
- Modify: `src/routes.rs`

### Step 1: Substituir PaneProxy por ProcessProxy no AppState

```rust
use crate::process_proxy::ProcessProxy;

pub struct AppState {
    pub config: AppConfig,
    pub session_mgr: SessionManager,
    pub tmux: TmuxDriver,         // manter para developer mode
    pub process_proxy: ProcessProxy,
    pub broadcast_tx: broadcast::Sender<ServerMessage>,
}

impl AppState {
    pub fn new(config: AppConfig) -> Self {
        let tmux = TmuxDriver::new();
        let session_mgr = SessionManager::new(config.clone(), tmux.clone());
        let (broadcast_tx, _) = broadcast::channel(256);
        let process_proxy = ProcessProxy::new(config.clone(), broadcast_tx.clone());

        Self {
            config,
            session_mgr,
            tmux,
            process_proxy,
            broadcast_tx,
        }
    }
}
```

### Step 2: Atualizar handle_client_message para ChatInput

Adicionar handler para `ClientMessage::ChatInput`:

```rust
ClientMessage::ChatInput { session_id, text } => {
    if let Err(e) = state.process_proxy.send_input(&session_id, &text).await {
        warn!(session_id = %session_id, "falha ao enviar chat input: {e}");
        send_server_msg(
            socket,
            &ServerMessage::Error {
                message: format!("chat input error: {e}"),
            },
        )
        .await;
    }
}
```

### Step 3: Atualizar CreateSession para usar ProcessProxy

Em `handle_client_message_tracked`, substituir a logica de tmux + send_keys por:

```rust
// Auto-start Claude Code via ProcessProxy (headless)
if let Err(e) = state
    .process_proxy
    .spawn_process(
        &session_id,
        info.working_dir.as_deref(),
        None, // sem prompt inicial -- usuario envia via ChatInput
    )
    .await
{
    warn!(session_id = %session_id, "falha ao spawnar Claude: {e}");
}
```

### Step 4: Atualizar DestroySession para matar processo

Adicionar apos `destroy_session`:

```rust
let _ = state.process_proxy.kill_process(&session_id).await;
```

### Step 5: Commit

```bash
git add src/routes.rs
git commit -m "feat(ccui-backend): routes.rs usa ProcessProxy em vez de PaneProxy"
```

---

## Task 6: Atualizar session.rs -- remover dependencia de tmux para output

**Files:**
- Modify: `src/session.rs`

### Step 1: Simplificar SessionInfo

Remover `main_pane_id` (nao ha mais panes). Manter `tmux_session` apenas para developer mode.

```rust
pub struct SessionInfo {
    pub id: String,
    pub tmux_session: String,     // manter para dev mode
    pub working_dir: Option<String>,
    pub case_id: Option<String>,
}
```

### Step 2: Atualizar metodos que referenciam main_pane_id

Remover `main_pane_id` de `SessionMetadata`, `from_info`, `into_info`, `create_session`, `recover_orphan_sessions`.

### Step 3: Commit

```bash
git add src/session.rs
git commit -m "refactor(ccui-backend): session.rs -- remover main_pane_id (sem panes)"
```

---

## Task 7: Deletar pane_proxy.rs

**Files:**
- Delete: `src/pane_proxy.rs`
- Modify: `src/lib.rs` (remover `pub mod pane_proxy;`)

### Step 1: Remover modulo e referencia

```bash
rm src/pane_proxy.rs
# Remover `pub mod pane_proxy;` de lib.rs
```

### Step 2: Commit

```bash
git add -A
git commit -m "refactor(ccui-backend): remover pane_proxy.rs (substituido por process_proxy)"
```

---

## Task 8: Simplificar tmux.rs

**Files:**
- Modify: `src/tmux.rs`

### Step 1: Remover metodos de pipe-pane

Remover: `pipe_pane`, `unpipe_pane`, `capture_pane`.
Manter: `new_session`, `kill_session`, `session_exists`, `list_sessions_with_prefix`, `send_keys` (para developer mode).

### Step 2: Commit

```bash
git add src/tmux.rs
git commit -m "refactor(ccui-backend): tmux.rs -- remover pipe-pane (desnecessario)"
```

---

## Task 9: Atualizar main.rs e team_watcher.rs

**Files:**
- Modify: `src/main.rs`
- Modify: `src/team_watcher.rs` (ajustar se necessario)

### Step 1: Remover referencia a PaneProxy de main.rs (se houver)

O main.rs atual nao referencia PaneProxy diretamente -- usa AppState::new(). Verificar que compila.

### Step 2: Verificar team_watcher.rs

O TeamWatcher emite `AgentJoined`/`AgentLeft` com `pane_id`. Na nova arquitetura, teammates podem usar ProcessProxy. Por enquanto, manter o TeamWatcher como esta -- ele monitora teammates que rodam em panes tmux (futuro: adaptar para processos).

### Step 3: Commit

```bash
git add src/main.rs src/team_watcher.rs
git commit -m "refactor(ccui-backend): main.rs e team_watcher.rs -- ajustes compilacao"
```

---

## Task 10: Cargo check e build

**Files:**
- Nenhum novo

### Step 1: Verificar compilacao

```bash
cd legal-workbench/ccui-backend
cargo check 2>&1
```

Esperado: sem erros.

### Step 2: Verificar clippy

```bash
cargo clippy -- -W clippy::pedantic 2>&1
```

Corrigir warnings.

### Step 3: Build release

```bash
cargo build --release 2>&1
```

### Step 4: Commit (se houver fixes)

```bash
git add -A
git commit -m "fix(ccui-backend): corrigir warnings clippy e erros de compilacao"
```

---

## Reconexao via Logs JSONL

**Nota de design (nao implementar nesta fase):**

Os logs JSONL do Claude Code ficam em `~/.claude/projects/*/`. Quando um cliente WS reconecta apos desconexao, o backend pode ler o log JSONL da sessao para reconstruir o historico. Isso sera implementado na Phase 3 como funcionalidade de "replay". O campo `claude_session_id` capturado no `ProcessState` permite localizar o arquivo de log correto.

---

## Migracao: Resumo Arquivo por Arquivo

| Arquivo | Acao | Detalhes |
|---------|------|----------|
| `claude_types.rs` | **CRIAR** | Tipos Rust para NDJSON stream-json |
| `process_proxy.rs` | **CRIAR** | Bridge child process <-> broadcast WS |
| `pane_proxy.rs` | **DELETAR** | Substituido por process_proxy |
| `message_part.rs` | **CRIAR** | Tipo MessagePart compartilhado (alinhado com frontend) |
| `ws.rs` | **MODIFICAR** | Adicionar ChatStart/ChatDelta/ChatEnd/ChatInit ao ServerMessage, ChatInput ao ClientMessage |
| `error.rs` | **MODIFICAR** | Adicionar variante Process |
| `config.rs` | **MODIFICAR** | Remover pane_log_dir/capture_poll_ms, adicionar process_start_timeout_secs |
| `routes.rs` | **MODIFICAR** | Trocar PaneProxy por ProcessProxy, handler ChatInput |
| `session.rs` | **MODIFICAR** | Remover main_pane_id |
| `tmux.rs` | **MODIFICAR** | Remover pipe_pane/unpipe_pane/capture_pane |
| `team_watcher.rs` | **MANTER** | Sem mudancas (futuro: adaptar para processos) |
| `main.rs` | **MANTER** | Compila via AppState::new() sem mudancas |
| `Cargo.toml` | **MANTER** | Deps atuais suficientes (tokio, serde, serde_json ja presentes) |

---

## Ordem de Implementacao

```
Task 1: claude_types.rs (tipos)
  |
  v
Task 2: ws.rs (protocolo)         Task 4: config.rs (config)
  |                                  |
  v                                  v
Task 3: process_proxy.rs ---------> Task 5: routes.rs (integracao)
                                     |
                                     v
                               Task 6: session.rs (simplificar)
                                     |
                                     v
                               Task 7: deletar pane_proxy.rs
                                     |
                                     v
                               Task 8: simplificar tmux.rs
                                     |
                                     v
                               Task 9: main.rs + team_watcher.rs
                                     |
                                     v
                               Task 10: cargo check + build
```

Tasks 1, 2 e 4 sao independentes e podem ser feitas em paralelo.
Tasks 3-10 sao sequenciais.

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Schema NDJSON muda entre versoes do Claude Code | Media | Alto | Usar `serde_json::Value` para campos extensiveis; `#[serde(default)]` em todos os opcionais; variante `Unknown` no enum |
| stdin flush nao funciona com Bun (oven-sh/bun#2423) | Alta (se usar Bun) | Critico | Sempre spawnar via `claude` que resolve para Node internamente; nunca usar `bun run claude` |
| Processo Claude nao encerra gracefully | Baixa | Medio | CancellationToken + child.kill() como fallback; timeout de 5s entre SIGTERM e SIGKILL |
| Stream-json input format diferente do documentado | Media | Alto | Testar com `claude -p --input-format stream-json` localmente antes de integrar; fallback para prompt como argumento CLI |
| Broadcast channel overflow (256 msgs) | Baixa | Baixo | broadcast::channel(256) e suficiente; se necessario, aumentar ou usar mpsc com fan-out manual |
| TeamWatcher assume pane_id para agentes | Media | Medio | Manter TeamWatcher como esta; na Phase 3, adicionar ProcessProxy para teammates tambem |
