//! Router HTTP e handlers WebSocket.

use std::sync::Arc;

use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
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

    loop {
        tokio::select! {
            // Mensagem vinda do cliente.
            client_msg = socket.recv() => {
                match client_msg {
                    Some(Ok(Message::Text(text))) => {
                        match serde_json::from_str::<ClientMessage>(&text) {
                            Ok(msg) => {
                                handle_client_message(&mut socket, &state, msg).await;
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
                    Ok(msg) => {
                        send_server_msg(&mut socket, &msg).await;
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
            match state
                .session_mgr
                .create_session(case_id.as_deref())
                .await
            {
                Ok(session_id) => {
                    info!(session_id = %session_id, "sessao criada");
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
