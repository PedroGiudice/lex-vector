//! Protocolo WebSocket: mensagens cliente -> servidor e servidor -> cliente.

use serde::{Deserialize, Serialize};

/// Mensagens enviadas pelo cliente ao servidor.
#[derive(Debug, Deserialize)]
#[serde(tag = "type")]
pub enum ClientMessage {
    /// Envia texto para um canal (pane).
    #[serde(rename = "input")]
    Input { channel: String, text: String },

    /// Redimensiona um canal (pane).
    #[serde(rename = "resize")]
    Resize {
        channel: String,
        cols: u32,
        rows: u32,
    },

    /// Solicita criacao de nova sessao.
    #[serde(rename = "create_session")]
    CreateSession {
        #[serde(default)]
        working_dir: Option<String>,
    },

    /// Solicita destruicao de sessao existente.
    #[serde(rename = "destroy_session")]
    DestroySession { session_id: String },

    /// Keepalive.
    #[serde(rename = "ping")]
    Ping,
}

/// Mensagens enviadas pelo servidor ao cliente.
#[derive(Debug, Serialize, Clone)]
#[serde(tag = "type")]
pub enum ServerMessage {
    /// Saida de um canal (pane).
    #[serde(rename = "output")]
    Output { channel: String, data: String },

    /// Confirmacao de sessao criada.
    #[serde(rename = "session_created")]
    SessionCreated { session_id: String },

    /// Notificacao de sessao encerrada.
    #[serde(rename = "session_ended")]
    SessionEnded { session_id: String },

    /// Agente entrou na sessao.
    #[serde(rename = "agent_joined")]
    AgentJoined {
        name: String,
        color: String,
        model: String,
        pane_id: String,
    },

    /// Agente saiu da sessao.
    #[serde(rename = "agent_left")]
    AgentLeft { name: String },

    /// Agente encerrou de forma inesperada.
    #[serde(rename = "agent_crashed")]
    AgentCrashed { name: String },

    /// Erro generico.
    #[serde(rename = "error")]
    Error { message: String },

    /// Resposta ao Ping.
    #[serde(rename = "pong")]
    Pong,
}
