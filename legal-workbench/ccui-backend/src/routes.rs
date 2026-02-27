//! Router HTTP e handlers WebSocket.

use std::sync::Arc;

use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Path, State,
    },
    http::StatusCode,
    response::IntoResponse,
    routing::get,
    Json, Router,
};
use serde_json::json;
use tokio::sync::broadcast;
use tower_http::cors::CorsLayer;
use tracing::{info, warn};

use crate::{
    config::AppConfig,
    pane_proxy::PaneProxy,
    session::SessionManager,
    tmux::TmuxDriver,
    ws::{ClientMessage, ServerMessage},
};

// ---------------------------------------------------------------------------
// Estado compartilhado
// ---------------------------------------------------------------------------

/// Estado da aplicacao compartilhado entre handlers.
#[derive(Clone)]
pub struct AppState {
    pub config: AppConfig,
    pub session_mgr: SessionManager,
    pub tmux: TmuxDriver,
    pub pane_proxy: PaneProxy,
    pub broadcast_tx: broadcast::Sender<ServerMessage>,
}

impl AppState {
    /// Cria o estado inicial da aplicacao.
    #[must_use]
    pub fn new(config: AppConfig) -> Self {
        let tmux = TmuxDriver::new();
        let session_mgr = SessionManager::new(config.clone(), tmux.clone());
        let (broadcast_tx, _) = broadcast::channel(256);
        let pane_proxy = PaneProxy::new(config.clone(), tmux.clone(), broadcast_tx.clone());

        Self {
            config,
            session_mgr,
            tmux,
            pane_proxy,
            broadcast_tx,
        }
    }
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

/// Constroi o `Router` principal da aplicacao.
pub fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/ws", get(ws_upgrade))
        .route("/api/sessions", get(list_sessions))
        .route("/api/cases", get(list_cases))
        .route("/api/sessions/{id}/channels", get(list_channels))
        .layer(CorsLayer::permissive())
        .with_state(Arc::new(state))
}

// ---------------------------------------------------------------------------
// Handlers HTTP
// ---------------------------------------------------------------------------

/// `GET /health` -- retorna `"ok"`.
async fn health() -> &'static str {
    "ok"
}

/// `GET /api/sessions` -- lista IDs das sessoes ativas.
#[allow(clippy::missing_errors_doc)]
async fn list_sessions(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let sessions = state.session_mgr.list_sessions().await;
    let ids: Vec<&str> = sessions.iter().map(|s| s.id.as_str()).collect();
    Json(json!({ "sessions": ids }))
}

/// `GET /api/sessions/{id}/channels` -- lista canais ativos de uma sessao.
///
/// Retorna 404 se a sessao nao existir.
async fn list_channels(
    Path(session_id): Path<String>,
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    if state.session_mgr.get_session(&session_id).await.is_none() {
        return (
            StatusCode::NOT_FOUND,
            Json(json!({ "error": "sessao nao encontrada" })),
        )
            .into_response();
    }

    let details = state.pane_proxy.list_channel_details().await;
    let channels: Vec<serde_json::Value> = details
        .into_iter()
        .map(|(name, pane_id)| json!({ "name": name, "pane_id": pane_id }))
        .collect();

    Json(json!({ "channels": channels })).into_response()
}

/// `GET /api/cases` -- lista casos disponiveis com metadados.
async fn list_cases(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let cases_dir = &state.config.cases_dir;
    let mut cases = Vec::new();

    if let Ok(entries) = std::fs::read_dir(cases_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if !path.is_dir() {
                continue;
            }

            let id = entry.file_name().to_string_lossy().to_string();
            let ready = path.join("knowledge.db").exists();

            let doc_count = path
                .join("base")
                .read_dir()
                .map(|rd| rd.flatten().filter(|e| e.path().is_file()).count())
                .unwrap_or(0);

            let last_modified = std::fs::metadata(&path)
                .and_then(|m| m.modified())
                .ok()
                .and_then(|t| {
                    let duration = t.duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
                    Some(duration.as_secs())
                });

            // Sessoes ativas apontando para este caso
            let active_sessions: Vec<String> = state
                .session_mgr
                .list_sessions()
                .await
                .iter()
                .filter(|s| {
                    s.working_dir
                        .as_ref()
                        .is_some_and(|wd| wd == path.to_str().unwrap_or_default())
                })
                .map(|s| s.id.clone())
                .collect();

            cases.push(json!({
                "id": id,
                "path": path.to_string_lossy(),
                "ready": ready,
                "doc_count": doc_count,
                "active_sessions": active_sessions,
                "last_modified": last_modified,
            }));
        }
    }

    Json(json!({ "cases": cases }))
}

// ---------------------------------------------------------------------------
// WebSocket upgrade
// ---------------------------------------------------------------------------

/// `GET /ws` -- upgrade para WebSocket.
async fn ws_upgrade(ws: WebSocketUpgrade, State(state): State<Arc<AppState>>) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_ws(socket, state))
}

// ---------------------------------------------------------------------------
// Handler WebSocket
// ---------------------------------------------------------------------------

async fn handle_ws(mut socket: WebSocket, state: Arc<AppState>) {
    let mut rx = state.broadcast_tx.subscribe();
    // Rastreia a sessao ativa desta conexao WS para resolver tmux_session de agentes.
    let mut current_session_id: Option<String> = None;

    loop {
        tokio::select! {
            // Mensagem vinda do cliente.
            client_msg = socket.recv() => {
                match client_msg {
                    Some(Ok(Message::Text(text))) => {
                        match serde_json::from_str::<ClientMessage>(&text) {
                            Ok(msg) => {
                                // Captura session_id ao criar sessao
                                if let ClientMessage::CreateSession { .. } = &msg {
                                    handle_client_message_tracked(
                                        &mut socket, &state, msg, &mut current_session_id
                                    ).await;
                                } else {
                                    handle_client_message(&mut socket, &state, msg).await;
                                }
                            }
                            Err(e) => {
                                warn!("mensagem invalida do cliente: {e}");
                                let err = ServerMessage::Error {
                                    message: format!("mensagem invalida: {e}"),
                                };
                                send_server_msg(&mut socket, &err).await;
                            }
                        }
                    }
                    Some(Ok(Message::Close(_))) | None => {
                        info!("cliente desconectou");
                        break;
                    }
                    Some(Ok(Message::Ping(payload))) => {
                        let _ = socket.send(Message::Pong(payload)).await;
                    }
                    Some(Ok(_)) => {
                        // binario ou outros -- ignorar
                    }
                    Some(Err(e)) => {
                        warn!("erro ao receber mensagem WebSocket: {e}");
                        break;
                    }
                }
            }

            // Mensagem de broadcast para enviar ao cliente.
            broadcast_msg = rx.recv() => {
                match broadcast_msg {
                    Ok(ref msg) => {
                        // Auto-registro de canais de teammates
                        match msg {
                            ServerMessage::AgentJoined { name, pane_id, .. } => {
                                if let Some(ref sid) = current_session_id {
                                    if let Some(info) = state.session_mgr.get_session(sid).await {
                                        if let Err(e) = state
                                            .pane_proxy
                                            .register_channel(name, &info.tmux_session, pane_id)
                                            .await
                                        {
                                            warn!(
                                                agent = %name,
                                                "falha ao auto-registrar canal de agente: {e}"
                                            );
                                        }
                                    }
                                }
                            }
                            ServerMessage::AgentLeft { name } => {
                                if let Err(e) = state.pane_proxy.unregister_channel(name).await {
                                    warn!(
                                        agent = %name,
                                        "falha ao desregistrar canal de agente: {e}"
                                    );
                                }
                            }
                            _ => {}
                        }
                        send_server_msg(&mut socket, msg).await;
                    }
                    Err(broadcast::error::RecvError::Lagged(n)) => {
                        warn!("cliente perdeu {n} mensagens de broadcast");
                    }
                    Err(broadcast::error::RecvError::Closed) => {
                        break;
                    }
                }
            }
        }
    }
}

/// Versao de `handle_client_message` que captura o session_id resultante.
async fn handle_client_message_tracked(
    socket: &mut WebSocket,
    state: &AppState,
    msg: ClientMessage,
    current_session_id: &mut Option<String>,
) {
    if let ClientMessage::CreateSession { ref case_id } = msg {
        match state.session_mgr.create_session(case_id.as_deref()).await {
            Ok(session_id) => {
                info!(session_id = %session_id, "sessao criada");
                *current_session_id = Some(session_id.clone());

                // Auto-registra canal "main" no pane_proxy
                if let Some(info) = state.session_mgr.get_session(&session_id).await {
                    if let Err(e) = state
                        .pane_proxy
                        .register_channel("main", &info.tmux_session, &info.main_pane_id)
                        .await
                    {
                        warn!(session_id = %session_id, "falha ao registrar canal main: {e}");
                    }

                    // Auto-start Claude Code
                    if let Err(e) = state
                        .tmux
                        .send_keys(
                            &info.tmux_session,
                            &info.main_pane_id,
                            "claude --dangerously-skip-permissions",
                        )
                        .await
                    {
                        warn!(session_id = %session_id, "falha ao iniciar Claude: {e}");
                    }
                }

                let _ = state.broadcast_tx.send(ServerMessage::SessionCreated {
                    session_id,
                    case_id: case_id.clone(),
                });
            }
            Err(e) => {
                warn!("falha ao criar sessao: {e}");
                send_server_msg(
                    socket,
                    &ServerMessage::Error {
                        message: e.to_string(),
                    },
                )
                .await;
            }
        }
    }
}

/// Envia uma `ServerMessage` serializada como texto JSON ao socket.
async fn send_server_msg(socket: &mut WebSocket, msg: &ServerMessage) {
    match serde_json::to_string(msg) {
        Ok(json) => {
            if let Err(e) = socket.send(Message::Text(json.into())).await {
                warn!("falha ao enviar mensagem ao cliente: {e}");
            }
        }
        Err(e) => {
            warn!("falha ao serializar ServerMessage: {e}");
        }
    }
}

/// Despacha uma `ClientMessage` para o handler correspondente.
async fn handle_client_message(socket: &mut WebSocket, state: &AppState, msg: ClientMessage) {
    match msg {
        ClientMessage::Ping => {
            send_server_msg(socket, &ServerMessage::Pong).await;
        }

        ClientMessage::CreateSession { case_id } => {
            match state.session_mgr.create_session(case_id.as_deref()).await {
                Ok(session_id) => {
                    info!(session_id = %session_id, "sessao criada");

                    // Auto-registra canal "main" no pane_proxy
                    if let Some(info) = state.session_mgr.get_session(&session_id).await {
                        if let Err(e) = state
                            .pane_proxy
                            .register_channel("main", &info.tmux_session, &info.main_pane_id)
                            .await
                        {
                            warn!(session_id = %session_id, "falha ao registrar canal main: {e}");
                        }

                        // Auto-start Claude Code
                        if let Err(e) = state
                            .tmux
                            .send_keys(
                                &info.tmux_session,
                                &info.main_pane_id,
                                "claude --dangerously-skip-permissions",
                            )
                            .await
                        {
                            warn!(session_id = %session_id, "falha ao iniciar Claude: {e}");
                        }
                    }

                    let _ = state.broadcast_tx.send(ServerMessage::SessionCreated {
                        session_id,
                        case_id,
                    });
                }
                Err(e) => {
                    warn!("falha ao criar sessao: {e}");
                    send_server_msg(
                        socket,
                        &ServerMessage::Error {
                            message: e.to_string(),
                        },
                    )
                    .await;
                }
            }
        }

        ClientMessage::DestroySession { session_id } => {
            match state.session_mgr.destroy_session(&session_id).await {
                Ok(()) => {
                    info!(session_id = %session_id, "sessao destruida");
                    let _ = state
                        .broadcast_tx
                        .send(ServerMessage::SessionEnded { session_id });
                }
                Err(e) => {
                    warn!("falha ao destruir sessao: {e}");
                    send_server_msg(
                        socket,
                        &ServerMessage::Error {
                            message: e.to_string(),
                        },
                    )
                    .await;
                }
            }
        }

        ClientMessage::Input { channel, text } => {
            if let Err(e) = state.pane_proxy.send_input(&channel, &text).await {
                warn!(channel = %channel, "falha ao enviar input: {e}");
                send_server_msg(
                    socket,
                    &ServerMessage::Error {
                        message: format!("input error: {e}"),
                    },
                )
                .await;
            }
        }

        ClientMessage::Resize {
            channel,
            cols,
            rows,
        } => {
            #[allow(clippy::cast_possible_truncation)]
            let (cols, rows) = (cols as u16, rows as u16);
            if let Err(e) = state.pane_proxy.resize_channel(&channel, cols, rows).await {
                warn!(channel = %channel, "falha ao resize: {e}");
            }
        }
    }
}
