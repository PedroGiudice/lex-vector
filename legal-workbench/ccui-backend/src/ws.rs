//! Protocolo WebSocket: mensagens cliente -> servidor e servidor -> cliente.

use serde::{Deserialize, Serialize};

use crate::message_part::MessagePart;

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
        case_id: Option<String>,
    },

    /// Solicita destruicao de sessao existente.
    #[serde(rename = "destroy_session")]
    DestroySession { session_id: String },

    /// Envia prompt para o Claude via stream-json input.
    #[serde(rename = "chat_input")]
    ChatInput { session_id: String, text: String },

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
    SessionCreated {
        session_id: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        case_id: Option<String>,
    },

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

    /// Inicio de uma nova mensagem do assistente.
    #[serde(rename = "chat_start")]
    ChatStart {
        message_id: String,
        session_id: String,
    },

    /// Parte incremental de uma mensagem (texto, thinking, `tool_use`, `tool_result`).
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

    /// Erro generico.
    #[serde(rename = "error")]
    Error { message: String },

    /// Resposta ao Ping.
    #[serde(rename = "pong")]
    Pong,
}
