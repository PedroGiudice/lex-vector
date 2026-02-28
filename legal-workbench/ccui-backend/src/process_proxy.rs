//! [`ProcessProxy`] -- bridge entre child process Claude Code (`stream-json`) e broadcast WS.
//!
//! Substitui o `PaneProxy`. Spawna `claude -p --output-format stream-json` como child process,
//! le stdout linha por linha (NDJSON), deserializa em `SDKMessage` e emite `ChatUpdate` no broadcast.

use std::collections::HashMap;
use std::sync::Arc;

use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::process::{Child, Command};
use tokio::sync::{broadcast, RwLock};
use tokio_util::sync::CancellationToken;

use crate::claude_types::{ContentBlock, SDKMessage};
use crate::config::AppConfig;
use crate::error::AppError;
use crate::message_part::{MessagePart, MessagePartMetadata, MessagePartType};
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
    /// # Errors
    ///
    /// Retorna `AppError::Process` se falhar ao spawnar o processo.
    pub async fn spawn_process(
        &self,
        session_id: &str,
        working_dir: Option<&str>,
        initial_prompt: Option<&str>,
    ) -> Result<(), AppError> {
        let mut cmd = Command::new(&self.config.claude_bin);
        cmd.arg("-p")
            .arg("--output-format")
            .arg("stream-json")
            .arg("--input-format")
            .arg("stream-json")
            .arg("--include-partial-messages")
            .arg("--permission-mode")
            .arg("bypassPermissions");

        for flag in &self.config.claude_flags {
            cmd.arg(flag);
        }

        if let Some(dir) = working_dir {
            cmd.current_dir(dir);
        }

        cmd.env("CLAUDECODE", "");

        cmd.stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());

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

        spawn_stdout_reader(self.tx.clone(), session_id, stdout, cancel, self.processes.clone());
        spawn_stderr_drain(session_id, stderr);
        Ok(())
    }

    /// Envia input para o processo Claude via stdin (`stream-json` format).
    ///
    /// # Errors
    ///
    /// Retorna `AppError::Process` se o processo nao existir ou stdin falhar.
    pub async fn send_input(&self, session_id: &str, text: &str) -> Result<(), AppError> {
        let mut guard = self.processes.write().await;
        let state = guard.get_mut(session_id).ok_or_else(|| {
            AppError::Process(format!("processo nao encontrado: {session_id}"))
        })?;

        let stdin = state.child.stdin.as_mut().ok_or_else(|| {
            AppError::Process("stdin nao disponivel".into())
        })?;

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

    /// Encerra o processo Claude de uma sessao.
    ///
    /// # Errors
    ///
    /// Sempre retorna `Ok` (best-effort kill).
    pub async fn kill_process(&self, session_id: &str) -> Result<(), AppError> {
        let mut guard = self.processes.write().await;
        if let Some(mut state) = guard.remove(session_id) {
            state.cancel.cancel();
            let _ = state.child.kill().await;
        }
        Ok(())
    }

    /// Lista sessoes com processos ativos.
    pub async fn list_sessions(&self) -> Vec<String> {
        self.processes.read().await.keys().cloned().collect()
    }
}

fn spawn_stdout_reader(
    tx: broadcast::Sender<ServerMessage>,
    session_id: &str,
    stdout: tokio::process::ChildStdout,
    cancel: CancellationToken,
    processes: Arc<RwLock<HashMap<String, ProcessState>>>,
) {
    let sid = session_id.to_owned();
    tokio::spawn(async move {
        let reader = BufReader::new(stdout);
        let mut lines = reader.lines();
        loop {
            tokio::select! {
                line = lines.next_line() => {
                    match line {
                        Ok(Some(line)) if !line.trim().is_empty() => {
                            match serde_json::from_str::<SDKMessage>(&line) {
                                Ok(msg) => emit_chat_update(&tx, &sid, &msg, &processes).await,
                                Err(e) => tracing::debug!(
                                    session_id = %sid,
                                    line = %line.chars().take(200).collect::<String>(),
                                    "NDJSON parse error: {e}"
                                ),
                            }
                        }
                        Ok(Some(_)) => {}
                        Ok(None) => { tracing::info!(session_id = %sid, "claude stdout EOF"); break; }
                        Err(e) => { tracing::warn!(session_id = %sid, "erro lendo stdout: {e}"); break; }
                    }
                }
                () = cancel.cancelled() => { tracing::debug!(session_id = %sid, "stdout reader cancelado"); break; }
            }
        }
        let _ = tx.send(ServerMessage::ChatEnd {
            message_id: format!("exit_{sid}"),
            session_id: sid,
        });
    });
}

fn spawn_stderr_drain(session_id: &str, stderr: tokio::process::ChildStderr) {
    let sid = session_id.to_owned();
    tokio::spawn(async move {
        let reader = BufReader::new(stderr);
        let mut lines = reader.lines();
        while let Ok(Some(line)) = lines.next_line().await {
            if !line.trim().is_empty() {
                tracing::debug!(session_id = %sid, stderr = %line);
            }
        }
    });
}

/// Converte `SDKMessage` em envelope `chat_start`/`chat_delta`/`chat_end` e emite no broadcast.
async fn emit_chat_update(
    tx: &broadcast::Sender<ServerMessage>,
    session_id: &str,
    msg: &SDKMessage,
    processes: &Arc<RwLock<HashMap<String, ProcessState>>>,
) {
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
                let part = content_block_to_part(block);
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

        SDKMessage::StreamEvent(evt) => {
            let message_id = evt.uuid.clone();
            if let Some(event_type) = evt.event.get("type").and_then(|v| v.as_str()) {
                if event_type == "content_block_delta" {
                    if let Some(delta) = evt.event.get("delta") {
                        let part = stream_delta_to_part(delta);
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

        SDKMessage::Result(_) | SDKMessage::User(_) => {}
    }
}

fn content_block_to_part(block: &ContentBlock) -> MessagePart {
    match block {
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
        ContentBlock::ToolResult {
            tool_use_id,
            content,
            is_error,
        } => MessagePart {
            kind: MessagePartType::ToolResult,
            content: serde_json::to_string(content).unwrap_or_default(),
            metadata: Some(MessagePartMetadata {
                tool_name: None,
                tool_id: Some(tool_use_id.clone()),
                is_error: *is_error,
                is_streaming: None,
            }),
        },
    }
}

fn stream_delta_to_part(delta: &serde_json::Value) -> Option<MessagePart> {
    let delta_type = delta.get("type").and_then(|v| v.as_str());
    match delta_type {
        Some("text_delta") => delta.get("text").and_then(|v| v.as_str()).map(|t| MessagePart {
            kind: MessagePartType::Text,
            content: t.to_owned(),
            metadata: Some(MessagePartMetadata {
                tool_name: None,
                tool_id: None,
                is_error: None,
                is_streaming: Some(true),
            }),
        }),
        Some("thinking_delta") => {
            delta
                .get("thinking")
                .and_then(|v| v.as_str())
                .map(|t| MessagePart {
                    kind: MessagePartType::Thinking,
                    content: t.to_owned(),
                    metadata: Some(MessagePartMetadata {
                        tool_name: None,
                        tool_id: None,
                        is_error: None,
                        is_streaming: Some(true),
                    }),
                })
        }
        _ => None,
    }
}
